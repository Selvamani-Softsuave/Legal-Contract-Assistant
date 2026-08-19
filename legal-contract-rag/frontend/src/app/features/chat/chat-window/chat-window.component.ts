import { Component, Input, OnInit, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ChatService } from '../../../core/services/chat.service';
import { CitationDrawerComponent } from '../citation-drawer/citation-drawer.component';
import { Contract, MessageResponse, SourceDTO } from '../../../core/models';

@Component({
    selector: 'app-chat-window',
    standalone: true,
    imports: [CommonModule, FormsModule, CitationDrawerComponent],
    template: `
    <div class="chat-container">
      <div class="chat-header">
        <div class="header-info">
          <h3>Grounded Legal Assistant</h3>
          <span class="scoping-badge" *ngIf="selectedContract">Scoped to: {{ selectedContract.name }}</span>
          <span class="scoping-badge global" *ngIf="!selectedContract">Scoped to: All Contracts</span>
        </div>
      </div>

      <div class="chat-messages">
        <div *ngIf="messages.length === 0" class="welcome-card">
          <p>💬 Ask questions about your legal contracts. Answers are strictly grounded in contract text with citations.</p>
        </div>

        <div *ngFor="let msg of messages" class="message-bubble" [class.user]="msg.role === 'user'" [class.assistant]="msg.role === 'assistant'">
          <div class="msg-author">{{ msg.role === 'user' ? 'You' : 'Legal AI Assistant' }}</div>
          <div class="msg-content">{{ msg.content }}</div>

          <div *ngIf="msg.sources && msg.sources.length > 0" class="citation-trigger">
            <button class="citation-btn" (click)="openSources(msg.sources)">
              📎 View {{ msg.sources.length }} Source Citation(s)
            </button>
          </div>
        </div>

        <div *ngIf="loading" class="typing-indicator">
          Generating grounded legal response...
        </div>
      </div>

      <div class="chat-input-area">
        <input type="text" 
               [(ngModel)]="questionText" 
               (keyup.enter)="send()"
               placeholder="Ask a legal question (e.g. What is the governing law and termination notice period?)..." 
               class="chat-input"
               [disabled]="loading" />
        <button class="send-btn" (click)="send()" [disabled]="loading || !questionText.trim()">Send</button>
      </div>

      <app-citation-drawer 
        [isOpen]="drawerOpen" 
        [sources]="activeSources" 
        (close)="drawerOpen = false">
      </app-citation-drawer>
    </div>
  `,
    styles: [`
    .chat-container { display: flex; flex-direction: column; height: 100%; background: #0f172a; border-radius: 8px; border: 1px solid #334155; overflow: hidden; }
    .chat-header { padding: 1rem; background: #1e293b; border-bottom: 1px solid #334155; display: flex; align-items: center; justify-content: space-between; }
    .scoping-badge { font-size: 0.75rem; background: rgba(59, 130, 246, 0.2); color: #60a5fa; padding: 2px 8px; border-radius: 12px; margin-top: 4px; display: inline-block; }
    .scoping-badge.global { background: rgba(16, 185, 129, 0.2); color: #34d399; }
    .chat-messages { flex: 1; padding: 1rem; overflow-y: auto; display: flex; flex-direction: column; gap: 1rem; }
    .welcome-card { padding: 1rem; background: #1e293b; border: 1px dashed #334155; border-radius: 6px; font-size: 0.85rem; color: #94a3b8; text-align: center; }
    .message-bubble {
      max-width: 80%; padding: 0.75rem 1rem; border-radius: 8px; font-size: 0.9rem; line-height: 1.4;
      &.user { align-self: flex-end; background: #3b82f6; color: #fff; }
      &.assistant { align-self: flex-start; background: #1e293b; border: 1px solid #334155; color: #f8fafc; }
    }
    .msg-author { font-size: 0.7rem; opacity: 0.8; margin-bottom: 4px; font-weight: 600; }
    .citation-trigger { margin-top: 0.5rem; }
    .citation-btn { background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.15); color: #60a5fa; font-size: 0.75rem; padding: 4px 8px; border-radius: 4px; cursor: pointer; }
    .typing-indicator { font-size: 0.8rem; color: #94a3b8; font-style: italic; }
    .chat-input-area { padding: 0.75rem; background: #1e293b; border-top: 1px solid #334155; display: flex; gap: 0.5rem; }
    .chat-input { flex: 1; background: #0f172a; border: 1px solid #334155; color: #fff; padding: 0.6rem 0.8rem; border-radius: 6px; }
    .send-btn { background: #3b82f6; color: #fff; border: none; padding: 0.6rem 1.2rem; border-radius: 6px; font-weight: 600; cursor: pointer; &:disabled { opacity: 0.5; } }
  `]
})
export class ChatWindowComponent implements OnInit, OnChanges {
    @Input() selectedContract: Contract | null = null;
    conversationId: string | null = null;
    messages: MessageResponse[] = [];
    questionText = '';
    loading = false;
    drawerOpen = false;
    activeSources: SourceDTO[] = [];

    constructor(private chatService: ChatService) { }

    ngOnInit(): void {
        this.initConversation();
    }

    ngOnChanges(changes: SimpleChanges): void {
        if (changes['selectedContract']) {
            this.initConversation();
        }
    }

    initConversation(): void {
        const scopedIds = this.selectedContract ? [this.selectedContract.id] : undefined;
        const title = this.selectedContract ? `Chat: ${this.selectedContract.name}` : 'Global Legal Chat';
        this.chatService.createConversation(title, scopedIds).subscribe(conv => {
            this.conversationId = conv.id;
            this.messages = [];
        });
    }

    send(): void {
        if (!this.questionText.trim() || !this.conversationId || this.loading) return;
        const q = this.questionText;
        this.questionText = '';

        // Append local user bubble
        const userMsg: MessageResponse = {
            id: Date.now().toString(),
            conversation_id: this.conversationId,
            role: 'user',
            content: q,
            sources: [],
            created_at: new Date().toISOString()
        };
        this.messages.push(userMsg);
        this.loading = true;

        const scopedIds = this.selectedContract ? [this.selectedContract.id] : undefined;
        this.chatService.sendMessage(this.conversationId, q, scopedIds).subscribe({
            next: (res) => {
                this.messages.push(res.message);
                this.loading = false;
            },
            error: () => {
                this.loading = false;
            }
        });
    }

    openSources(sources: SourceDTO[]): void {
        this.activeSources = sources;
        this.drawerOpen = true;
    }
}
