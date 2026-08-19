import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Contract, ContractCreate } from '../models';

@Injectable({
    providedIn: 'root'
})
export class ContractService {
    private apiUrl = '/api/v1/contracts';

    constructor(private http: HttpClient) { }

    getContracts(skip = 0, limit = 100, status?: string): Observable<Contract[]> {
        let params = new HttpParams().set('skip', skip).set('limit', limit);
        if (status) {
            params = params.set('status', status);
        }
        return this.http.get<Contract[]>(this.apiUrl, { params });
    }

    getContract(id: string): Observable<Contract> {
        return this.http.get<Contract>(`${this.apiUrl}/${id}`);
    }

    createContract(data: ContractCreate): Observable<Contract> {
        return this.http.post<Contract>(this.apiUrl, data);
    }

    deleteContract(id: string): Observable<void> {
        return this.http.delete<void>(`${this.apiUrl}/${id}`);
    }
}
