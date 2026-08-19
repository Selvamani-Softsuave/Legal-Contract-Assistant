import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { SourceDTO } from '../../../core/models';

@Component({
    selector: 'app-citation-drawer',
    standalone: true,
    imports: [CommonModule],
    template: `
    <div class="drawer-backdrop" *ngIf="isOpen" (click)="close.emit()"></div>
    <div class="drawer-panel" [class.open]="isOpen">
      <div class="drawer-header">
        <h3>Source Citations ({{ sources.length }})</h3>
        <button class="close-btn" (click)="close.emit()">✕</button>
      </div>

      <div class="drawer-body">
        <div *ngFor="let src of sources; let i = index" class="citation-card">
          <div class="citation-title">
            <span class="badge">Source #{{ i + 1 }}</span>
            <strong>{{ src.document_name }}</strong>
          </div>
          
          <div class="citation-meta">
            <span *ngIf="src.page_number">Page {{ src.page_number }}</span>
            <span *ngIf="src.section">• {{ src.section }}</span>
            <span *ngIf="src.clause">• Clause: {{ src.clause }}</span>
          </div>

          <div *ngIf="src.relevance_score !== undefined" class="score-bar">
            <span>Relevance Distance: {{ src.relevance_score.toFixed(3) }}</span>
          </div>
        </div>
      </div>
    </div>
  `,
    styles: [`
    .drawer-backdrop { position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 1100; }
    .drawer-panel {
      position: fixed; top: 0; right: 0; bottom: 0; width: 380px; background: #0f172a;
      border-left: 1px solid #334155; z-index: 1200; transform: translateX(100%);
      transition: transform 0.3s ease; display: flex; flex-direction: column;
      &.open { transform: translateX(0); }
    }
    .drawer-header { padding: 1rem; border-bottom: 1px solid #334155; display: flex; justify-content: space-between; align-items: center; }
    .close-btn { background: none; border: none; color: #94a3b8; font-size: 1.2rem; cursor: pointer; }
    .drawer-body { padding: 1rem; overflow-y: auto; flex: 1; }
    .citation-card { background: #1e293b; border: 1px solid #334155; border-radius: 6px; padding: 0.75rem; margin-bottom: 0.75rem; }
    .citation-title { display: flex; align-items: center; gap: 0.5rem; font-size: 0.85rem; margin-bottom: 4px; }
    .badge { background: #3b82f6; color: #fff; font-size: 0.7rem; padding: 2px 6px; border-radius: 4px; }
    .citation-meta { font-size: 0.75rem; color: #94a3b8; margin-bottom: 6px; }
    .score-bar { font-size: 0.7rem; color: #64748b; }
  `]
})
export class CitationDrawerComponent {
    @Input() isOpen = false;
    @Input() sources: SourceDTO[] = [];
    @Output() close = new EventEmitter<void>();
}
