import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ContractListComponent } from './features/contracts/contract-list/contract-list.component';
import { ContractDetailComponent } from './features/contracts/contract-detail/contract-detail.component';
import { ChatWindowComponent } from './features/chat/chat-window/chat-window.component';
import { Contract } from './core/models';

@Component({
    selector: 'app-root',
    standalone: true,
    imports: [CommonModule, ContractListComponent, ContractDetailComponent, ChatWindowComponent],
    template: `
    <div class="app-container">
      <header class="enterprise-header">
        <div class="brand-logo">
          <span>⚖️ Enterprise Legal RAG</span>
          <span class="badge">Enterprise v2.0</span>
        </div>
        <div class="header-status">
          <span class="status-chip completed">● System Ready</span>
        </div>
      </header>

      <main class="main-layout">
        <div class="sidebar">
          <app-contract-list (contractSelected)="onContractSelected($event)"></app-contract-list>
        </div>

        <div class="center-content">
          <app-contract-detail [contract]="selectedContract"></app-contract-detail>
        </div>

        <div class="chat-sidebar">
          <app-chat-window [selectedContract]="selectedContract"></app-chat-window>
        </div>
      </main>
    </div>
  `,
    styles: [`
    .main-layout { display: grid; grid-template-columns: 320px 1fr 420px; gap: 1rem; padding: 1rem; height: calc(100vh - 64px); box-sizing: border-box; }
    .sidebar { overflow-y: auto; background: rgba(15,23,42,0.6); border-radius: 8px; border: 1px solid #334155; }
    .center-content { overflow-y: auto; }
    .chat-sidebar { height: 100%; }
    @media (max-width: 1200px) {
      .main-layout { grid-template-columns: 1fr 1fr; }
      .sidebar { display: none; }
    }
  `]
})
export class AppComponent {
    selectedContract: Contract | null = null;

    onContractSelected(contract: Contract): void {
        this.selectedContract = contract;
    }
}
