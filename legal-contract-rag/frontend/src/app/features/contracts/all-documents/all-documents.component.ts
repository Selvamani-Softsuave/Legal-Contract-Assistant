import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { DocumentService } from '../../../core/services/document.service';
import { Document } from '../../../core/models';

@Component({
  selector: 'app-all-documents',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './all-documents.component.html',
  styleUrls: ['./all-documents.component.scss']
})
export class AllDocumentsComponent implements OnInit {
  documents: Document[] = [];
  loading = false;
  searchQuery = '';

  constructor(private documentService: DocumentService) { }

  ngOnInit(): void {
    this.loadAllDocuments();
  }

  loadAllDocuments(): void {
    this.loading = true;
    this.documentService.getAllDocuments().subscribe({
      next: (docs) => {
        this.documents = docs;
        this.loading = false;
      },
      error: () => {
        this.documents = [];
        this.loading = false;
      }
    });
  }

  get filteredDocuments(): Document[] {
    if (!this.searchQuery.trim()) return this.documents;
    const q = this.searchQuery.toLowerCase();
    return this.documents.filter(d => 
      d.file_name.toLowerCase().includes(q) ||
      (d.contract_name && d.contract_name.toLowerCase().includes(q)) ||
      (d.file_type && d.file_type.toLowerCase().includes(q)) ||
      (d.status && d.status.toLowerCase().includes(q))
    );
  }

  getFileIcon(fileType: string): string {
    const t = (fileType || '').toLowerCase();
    if (t === 'pdf') return '📕';
    if (t === 'docx' || t === 'doc') return '📘';
    if (t === 'txt') return '📄';
    return '📁';
  }

  reprocess(docId: string): void {
    this.documentService.reprocessDocument(docId).subscribe(() => {
      this.loadAllDocuments();
    });
  }

  deleteDoc(docId: string): void {
    if (confirm('Are you sure you want to delete this document and remove it from vector search?')) {
      this.documentService.deleteDocument(docId).subscribe(() => {
        this.loadAllDocuments();
      });
    }
  }
}
