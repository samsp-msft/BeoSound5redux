import { Component, inject, computed } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { NavStackComponent } from './nav-stack.component';
import { NavService } from './nav.service';
import { InputService } from './input/input.service';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, NavStackComponent, CommonModule],
  template: `
    <div class="beosound-container">
      <!-- Background Image -->
      <div class="app-background" *ngIf="backgroundUrl()" [style.backgroundImage]="'url(' + backgroundUrl() + ')'"></div>
      <div class="app-overlay"></div>

      <div class="dial-obstruction"></div>
      
      <div class="nav-stack">
        <app-nav-stack></app-nav-stack>
      </div>

      <router-outlet />
    </div>
  `,
  styles: [`
    .beosound-container {
      position: relative;
      width: 1024px;
      height: 768px;
      overflow: hidden;
      background: #000;
    }

    .app-background {
      position: absolute;
      inset: 0;
      background-size: cover;
      background-position: center;
      filter: blur(40px) brightness(0.4) saturate(1.2);
      transform: scale(1.1);
      transition: background-image 1.5s ease-in-out;
      z-index: 0;
    }

    .app-overlay {
      position: absolute;
      inset: 0;
      background: radial-gradient(circle at 90% 50%, rgba(0,0,0,0) 0%, rgba(0,0,0,0.8) 100%);
      z-index: 1;
      pointer-events: none;
    }

    .nav-stack {
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      z-index: 10;
    }

    .dial-obstruction {
      position: absolute;
      right: -200px;
      top: 50%;
      width: 400px;
      height: 400px;
      background: #000;
      border-radius: 50%;
      transform: translateY(-50%);
      z-index: 100;
      box-shadow: 0 0 100px rgba(0,0,0,1);
    }
  `]
})
export class App {
  title = 'beosound5redux';
  private navService = inject(NavService);
  
  backgroundUrl = computed(() => {
    const stack = this.navService.navStackData();
    if (stack.length > 0) {
      const active = stack[stack.length - 1];
      if (active.viewType === 'NOW_PLAYING' && active.items.length > 0) {
        return active.items[0].images?.landscape_large || active.items[0].images?.landscape_small || null;
      }
    }
    return null;
  });

  constructor() {
    inject(InputService).initialize();
  }
}
