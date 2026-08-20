import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ContractListComponent } from './features/contracts/contract-list/contract-list.component';
import { ContractDetailComponent } from './features/contracts/contract-detail/contract-detail.component';
import { AllDocumentsComponent } from './features/contracts/all-documents/all-documents.component';
import { ChatWindowComponent } from './features/chat/chat-window/chat-window.component';
import { Contract } from './core/models';

@Component({
    selector: 'app-root',
    standalone: true,
    imports: [
        CommonModule, 
        ContractListComponent, 
        ContractDetailComponent, 
        AllDocumentsComponent,
        ChatWindowComponent
    ],
    templateUrl: './app.component.html',
    styleUrls: ['./app.component.scss']
})
export class AppComponent {
    selectedContract: Contract | null = null;
    activeTab: 'contracts' | 'documents' | 'chat' = 'contracts';

    onContractSelected(contract: Contract): void {
        this.selectedContract = contract;
    }
}
