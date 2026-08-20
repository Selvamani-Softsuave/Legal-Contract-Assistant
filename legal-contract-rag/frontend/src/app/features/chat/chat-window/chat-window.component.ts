import { Component, Input, OnInit, OnChanges, SimpleChanges, ViewChild, ElementRef, AfterViewChecked } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ChatService } from '../../../core/services/chat.service';
import { CitationDrawerComponent } from '../citation-drawer/citation-drawer.component';
import { Contract, MessageResponse, SourceDTO, Conversation } from '../../../core/models';

@Component({
    selector: 'app-chat-window',
    standalone: true,
    imports: [CommonModule, FormsModule, CitationDrawerComponent],
    templateUrl: './chat-window.component.html',
    styleUrls: ['./chat-window.component.scss']
})
export class ChatWindowComponent implements OnInit, OnChanges, AfterViewChecked {
    @Input() selectedContract: Contract | null = null;
    @ViewChild('messagesContainer') private messagesContainer?: ElementRef;

    conversationId: string | null = null;
    activeConversationTitle = '';
    conversations: Conversation[] = [];
    messages: MessageResponse[] = [];
    questionText = '';
    loading = false;
    drawerOpen = false;
    showHistoryDrawer = false;
    activeSources: SourceDTO[] = [];
    private shouldScrollToBottom = false;

    constructor(private chatService: ChatService) { }

    ngOnInit(): void {
        this.loadConversations();
    }

    ngOnChanges(changes: SimpleChanges): void {
        if (changes['selectedContract']) {
            this.resetToDraftState();
        }
    }

    ngAfterViewChecked(): void {
        if (this.shouldScrollToBottom) {
            this.scrollToBottom();
            this.shouldScrollToBottom = false;
        }
    }

    loadConversations(): void {
        this.chatService.getConversations().subscribe(convs => {
            this.conversations = convs;
            if (convs.length > 0 && !this.conversationId) {
                this.selectConversation(convs[0]);
            } else if (!this.conversationId) {
                this.resetToDraftState();
            }
        });
    }

    resetToDraftState(): void {
        this.conversationId = null;
        this.messages = [];
        this.activeConversationTitle = this.selectedContract
            ? `Chat: ${this.selectedContract.name}`
            : 'New Conversation';
    }

    startNewChat(): void {
        this.resetToDraftState();
    }

    toggleHistory(): void {
        this.showHistoryDrawer = !this.showHistoryDrawer;
        if (this.showHistoryDrawer) {
            this.loadConversations();
        }
    }

    selectConversation(conv: Conversation): void {
        this.conversationId = conv.id;
        this.activeConversationTitle = conv.title;
        this.loading = true;
        this.chatService.getConversationMessages(conv.id).subscribe({
            next: (msgs) => {
                this.messages = msgs;
                this.loading = false;
                this.shouldScrollToBottom = true;
            },
            error: () => {
                this.messages = [];
                this.loading = false;
            }
        });
    }

    deleteConversation(event: Event, convId: string): void {
        event.stopPropagation();
        this.chatService.deleteConversation(convId).subscribe(() => {
            this.conversations = this.conversations.filter(c => c.id !== convId);
            if (this.conversationId === convId) {
                if (this.conversations.length > 0) {
                    this.selectConversation(this.conversations[0]);
                } else {
                    this.resetToDraftState();
                }
            }
        });
    }

    usePrompt(promptText: string): void {
        this.questionText = promptText;
        this.send();
    }

    onEnterPress(event: any): void {
        if (!event.shiftKey) {
            event.preventDefault();
            this.send();
        }
    }

    send(): void {
        if (!this.questionText.trim() || this.loading) return;
        const q = this.questionText.trim();
        this.questionText = '';

        if (!this.conversationId) {
            const scopedIds = this.selectedContract ? [this.selectedContract.id] : undefined;
            const title = this.selectedContract
                ? `Chat: ${this.selectedContract.name}`
                : (q.length > 30 ? q.substring(0, 30) + '...' : q);

            this.loading = true;
            this.chatService.createConversation(title, scopedIds).subscribe({
                next: (conv) => {
                    this.conversationId = conv.id;
                    this.activeConversationTitle = conv.title;
                    this.conversations.unshift(conv);
                    this.executeSendMessage(conv.id, q);
                },
                error: () => {
                    this.loading = false;
                }
            });
        } else {
            this.executeSendMessage(this.conversationId, q);
        }
    }

    private executeSendMessage(convId: string, question: string): void {
        const userMsg: MessageResponse = {
            id: Date.now().toString(),
            conversation_id: convId,
            role: 'user',
            content: question,
            sources: [],
            created_at: new Date().toISOString()
        };
        this.messages.push(userMsg);
        this.loading = true;
        this.shouldScrollToBottom = true;

        const scopedIds = this.selectedContract ? [this.selectedContract.id] : undefined;
        this.chatService.sendMessage(convId, question, scopedIds).subscribe({
            next: (res) => {
                this.messages.push(res.message);
                this.loading = false;
                this.shouldScrollToBottom = true;
            },
            error: (err) => {
                this.messages.push({
                    id: Date.now().toString(),
                    conversation_id: convId,
                    role: 'assistant',
                    content: 'Error connecting to RAG assistant. Please check your backend service.',
                    sources: [],
                    created_at: new Date().toISOString()
                });
                this.loading = false;
                this.shouldScrollToBottom = true;
            }
        });
    }

    openSources(sources: SourceDTO[]): void {
        this.activeSources = sources;
        this.drawerOpen = true;
    }

    private scrollToBottom(): void {
        try {
            if (this.messagesContainer) {
                this.messagesContainer.nativeElement.scrollTop = this.messagesContainer.nativeElement.scrollHeight;
            }
        } catch (err) { }
    }
}
