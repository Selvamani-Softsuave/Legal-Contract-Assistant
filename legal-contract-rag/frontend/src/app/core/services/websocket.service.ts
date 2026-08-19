import { Injectable, NgZone } from '@angular/core';
import { Observable, Subject } from 'rxjs';

export interface WsMessage {
    type: string;
    [key: string]: any;
}

@Injectable({
    providedIn: 'root'
})
export class WebSocketService {
    private socket: WebSocket | null = null;
    private messageSubject = new Subject<WsMessage>();

    public messages$: Observable<WsMessage> = this.messageSubject.asObservable();

    constructor(private zone: NgZone) {
        this.connect();
    }

    private connect(): void {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        // Use current host which natively routes through the nginx proxy or angular proxy
        const url = `${protocol}//${window.location.host}/api/v1/ws/events`;

        this.socket = new WebSocket(url);

        this.socket.onmessage = (event) => {
            this.zone.run(() => {
                try {
                    const data = JSON.parse(event.data);
                    this.messageSubject.next(data);
                } catch (e) {
                    console.error("Invalid WS message format", event.data);
                }
            });
        };

        this.socket.onclose = () => {
            // Reconnect logic
            setTimeout(() => this.zone.run(() => this.connect()), 5000);
        };

        this.socket.onerror = (err) => {
            console.error("WS error:", err);
        };
    }
}
