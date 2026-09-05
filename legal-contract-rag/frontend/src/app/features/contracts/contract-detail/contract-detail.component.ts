import { Component, Input, OnChanges, SimpleChanges, OnDestroy, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DocumentService } from '../../../core/services/document.service';
import { Contract, Document } from '../../../core/models';
import { Subscription, interval } from 'rxjs';
import { WebSocketService } from '../../../core/services/websocket.service';

const NON_TERMINAL_STATUSES = new Set(['Queued', 'Processing']);
const POLL_INTERVAL_MS = 5000;

@Component({
  selector: 'app-contract-detail',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div *ngIf="contract" class="contract-detail-container">
      <div class="detail-header">
        <div>
          <h2>{{ contract.name }}</h2>
          <p class="subtitle">{{ contract.contract_type }} • {{ contract.governing_law || 'No Jurisdiction' }}</p>
        </div>
        <div class="upload-btn-wrapper">
          <button class="btn primary">+ Upload Document</button>
          <input type="file" (change)="onFileSelected($event)" accept=".pdf,.docx,.txt" />
        </div>
      </div>

      <div class="documents-section">
        <h3>Associated Documents ({{ documents.length }})</h3>
        
        <div *ngIf="uploading" class="uploading-banner">
          Uploading and queuing document...
        </div>

        <table *ngIf="documents.length > 0; else noDocs" class="doc-table">
          <thead>
            <tr>
              <th>File Name</th>
              <th>Size</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let doc of documents">
              <td><strong>{{ doc.file_name }}</strong></td>
              <td>{{ (doc.file_size / 1024).toFixed(1) }} KB</td>
              <td><span class="status-chip" [class]="doc.status.toLowerCase()">{{ doc.status }}</span></td>
              <td class="action-cell">
                <button class="icon-btn" (click)="reprocess(doc.id)" title="Reprocess">🔄</button>
                <button class="icon-btn danger" (click)="deleteDoc(doc.id)" title="Delete">🗑️</button>
              </td>
            </tr>
          </tbody>
        </table>

        <ng-template #noDocs>
          <p class="empty-msg">No documents uploaded yet. Upload a PDF, DOCX, or TXT contract file.</p>
        </ng-template>
      </div>
    </div>
  `,
  styles: [`
    .contract-detail-container { padding: 1rem; background: var(--card-bg, #1e293b); border-radius: 8px; border: 1px solid #334155; }
    .detail-header { display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 1px solid #334155; padding-bottom: 1rem; margin-bottom: 1rem; }
    .subtitle { font-size: 0.85rem; color: #94a3b8; margin-top: 4px; }
    .upload-btn-wrapper { position: relative; overflow: hidden; display: inline-block; }
    .upload-btn-wrapper input[type=file] { position: absolute; left: 0; top: 0; opacity: 0; cursor: pointer; height: 100%; width: 100%; }
    .btn { padding: 0.5rem 1rem; border-radius: 6px; border: none; font-weight: 600; cursor: pointer; &.primary { background: #3b82f6; color: #fff; } }
    .doc-table { width: 100%; border-collapse: collapse; margin-top: 1rem; }
    .doc-table th, .doc-table td { padding: 0.75rem; text-align: left; border-bottom: 1px solid #334155; font-size: 0.85rem; }
    .doc-table th { background: #0f172a; color: #94a3b8; font-weight: 600; }
    .uploading-banner { padding: 0.5rem; background: rgba(59,130,246,0.2); color: #60a5fa; border-radius: 4px; font-size: 0.85rem; margin-bottom: 1rem; }
    .empty-msg { font-size: 0.85rem; color: #94a3b8; font-style: italic; }
    .action-cell { display: flex; gap: 0.5rem; }
    .icon-btn { background: none; border: none; cursor: pointer; font-size: 1rem; }
  `]
})
export class ContractDetailComponent implements OnChanges, OnDestroy, OnInit {
  @Input() contract: Contract | null = null;
  documents: Document[] = [];
  uploading = false;
  private wsSub?: Subscription;
  private pollSub?: Subscription;

  constructor(private documentService: DocumentService, private wsService: WebSocketService) { }

  ngOnInit(): void {
    this.wsSub = this.wsService.messages$.subscribe(msg => {
      if (msg.type === 'JOB_UPDATE' && this.contract && msg['document_id']) {
        this.loadDocuments();
      }
    });
    // Fallback safety net: WebSocket delivery is best-effort (dropped connections,
    // processor crashes before it can notify, etc). Poll while anything is in-flight
    // so the UI never gets stuck showing "Queued"/"Processing" forever.
    this.pollSub = interval(POLL_INTERVAL_MS).subscribe(() => {
      if (this.hasPendingDocuments()) {
        this.loadDocuments();
      }
    });
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['contract'] && this.contract) {
      this.loadDocuments();
    }
  }

  ngOnDestroy(): void {
    if (this.wsSub) {
      this.wsSub.unsubscribe();
    }
    if (this.pollSub) {
      this.pollSub.unsubscribe();
    }
  }

  private hasPendingDocuments(): boolean {
    return this.documents.some(d => NON_TERMINAL_STATUSES.has(d.status));
  }

  loadDocuments(): void {
    if (!this.contract) return;
    this.documentService.getContractDocuments(this.contract.id).subscribe(docs => {
      this.documents = docs;
    });
  }

  onFileSelected(event: any): void {
    const file: File = event.target.files[0];
    if (!file) return;

    const maxMB = 25;
    if (file.size > maxMB * 1024 * 1024) {
      alert(`File size (${(file.size / (1024 * 1024)).toFixed(1)}MB) exceeds maximum limit of ${maxMB}MB.`);
      event.target.value = '';
      return;
    }

    if (this.contract) {
      this.uploading = true;
      this.documentService.uploadDocument(this.contract.id, file).subscribe({
        next: () => {
          this.uploading = false;
          this.loadDocuments();
        },
        error: (err) => {
          this.uploading = false;
          alert(err.error?.detail || 'Failed to upload document. Please check file size and format.');
        }
      });
    }
  }

  reprocess(docId: string): void {
    this.documentService.reprocessDocument(docId).subscribe(() => {
      this.loadDocuments();
    });
  }

  deleteDoc(docId: string): void {
    this.documentService.deleteDocument(docId).subscribe(() => {
      this.loadDocuments();
    });
  }
}
