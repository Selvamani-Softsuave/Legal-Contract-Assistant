import { Component, OnInit, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ContractService } from '../../../core/services/contract.service';
import { Contract, ContractCreate } from '../../../core/models';

@Component({
  selector: 'app-contract-list',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="contract-list-container">
      <div class="header-actions">
        <h2>Contract Repository</h2>
        <button class="btn primary" (click)="showNewModal = true">+ New Contract</button>
      </div>

      <div class="contract-grid">
        <div *ngFor="let contract of contracts" 
             class="contract-card"
             [class.active]="selectedContractId === contract.id"
             (click)="selectContract(contract)">
          <div class="card-header">
            <h3>{{ contract.name }}</h3>
            <span class="status-chip" [class]="contract.status.toLowerCase()">{{ contract.status }}</span>
          </div>
          <p class="contract-meta">
            <span><strong>Type:</strong> {{ contract.contract_type || 'N/A' }}</span> | 
            <span><strong>Law:</strong> {{ contract.governing_law || 'N/A' }}</span>
          </p>
          <p class="contract-desc">{{ contract.description || 'No description provided.' }}</p>
        </div>
      </div>

      <!-- New Contract Modal -->
      <div *ngIf="showNewModal" class="modal-overlay">
        <div class="modal-content">
          <h3>Create New Legal Contract</h3>
          <form (ngSubmit)="createContract()">
            <div class="form-group">
              <label>Contract Title *</label>
              <input type="text" [(ngModel)]="newContract.name" name="name" required class="form-control" />
            </div>
            <div class="form-group">
              <label>Contract Type</label>
              <input type="text" [(ngModel)]="newContract.contract_type" name="contract_type" placeholder="e.g. Master Services Agreement" class="form-control" />
            </div>
            <div class="form-group">
              <label>Governing Law</label>
              <input type="text" [(ngModel)]="newContract.governing_law" name="governing_law" placeholder="e.g. Delaware, USA" class="form-control" />
            </div>
            <div class="form-group">
              <label>Description</label>
              <textarea [(ngModel)]="newContract.description" name="description" class="form-control"></textarea>
            </div>
            <div class="modal-actions">
              <button type="button" class="btn secondary" (click)="showNewModal = false">Cancel</button>
              <button type="submit" class="btn primary">Create</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .contract-list-container { padding: 1rem; }
    .header-actions { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
    .contract-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1rem; }
    .contract-card {
      background: var(--card-bg, #1e293b);
      border: 1px solid var(--border-color, #334155);
      border-radius: 8px;
      padding: 1rem;
      cursor: pointer;
      transition: all 0.2s ease;
      &:hover { border-color: var(--primary-accent, #3b82f6); transform: translateY(-2px); }
      &.active { border-color: var(--primary-accent, #3b82f6); background: rgba(59, 130, 246, 0.1); }
    }
    .card-header { display: flex; justify-content: space-between; align-items: flex-start; }
    .contract-meta { font-size: 0.8rem; color: var(--text-muted, #94a3b8); margin: 0.5rem 0; }
    .contract-desc { font-size: 0.85rem; color: #cbd5e1; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
    .btn {
      padding: 0.5rem 1rem; border-radius: 6px; border: none; font-weight: 600; cursor: pointer;
      &.primary { background: #3b82f6; color: #fff; }
      &.secondary { background: #475569; color: #fff; }
    }
    .modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.7); display: flex; align-items: center; justify-content: center; z-index: 1000; }
    .modal-content { background: #1e293b; padding: 1.5rem; border-radius: 8px; width: 400px; border: 1px solid #334155; }
    .form-group { margin-bottom: 1rem; display: flex; flex-direction: column; gap: 4px; }
    .form-control { background: #0f172a; border: 1px solid #334155; color: #fff; padding: 0.5rem; border-radius: 4px; }
    .modal-actions { display: flex; justify-content: flex-end; gap: 0.5rem; }
  `]
})
export class ContractListComponent implements OnInit {
  contracts: Contract[] = [];
  selectedContractId: string | null = null;
  showNewModal = false;
  newContract: ContractCreate = { name: '', contract_type: '', governing_law: '', description: '' };

  @Output() contractSelected = new EventEmitter<Contract>();

  constructor(private contractService: ContractService) { }

  ngOnInit(): void {
    this.loadContracts();
  }

  loadContracts(): void {
    this.contractService.getContracts().subscribe(data => {
      this.contracts = data;
      if (this.contracts.length > 0 && !this.selectedContractId) {
        this.selectContract(this.contracts[0]);
      }
    });
  }

  selectContract(contract: Contract): void {
    this.selectedContractId = contract.id;
    this.contractSelected.emit(contract);
  }

  createContract(): void {
    if (!this.newContract.name) return;
    this.contractService.createContract(this.newContract).subscribe(created => {
      this.showNewModal = false;
      this.newContract = { name: '', contract_type: '', governing_law: '', description: '' };
      this.loadContracts();
      this.selectContract(created);
    });
  }
}
