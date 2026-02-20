import { Injectable, inject, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { NavService } from '../nav.service';

@Injectable({
  providedIn: 'root'
})
export class InputService {
  private navService = inject(NavService);
  private isBrowser = isPlatformBrowser(inject(PLATFORM_ID));

  public initialize(): void {
    if (this.isBrowser) {
      console.log('InputService: Initializing event listeners...');
      window.addEventListener('keydown', (e) => {
        console.log('InputService: KeyDown event:', e.key);
        this.onKeyDown(e);
      });
      window.addEventListener('wheel', (e) => {
        console.log('InputService: Wheel event, deltaY:', e.deltaY);
        this.onWheel(e);
      }, { passive: false });
    }
  }

  private onWheel(event: WheelEvent): void {
    if (Math.abs(event.deltaY) > 5) {
      this.navService.moveSelection(event.deltaY > 0 ? 1 : -1);
    }
    event.preventDefault();
  }

  private onKeyDown(event: KeyboardEvent): void {
    switch (event.key) {
      case 'PageUp':
        this.navService.moveRootSelection(-1);
        break;
      case 'PageDown':
        this.navService.moveRootSelection(1);
        break;
      case 'ArrowUp':
        this.navService.moveSelection(-1);
        break;
      case 'ArrowDown':
        this.navService.moveSelection(1);
        break;
      case 'ArrowRight':
      case 'Enter':
        this.navService.navigateIn();
        break;
      case 'ArrowLeft':
      case 'Backspace': // Corrected from BackSpace
      case 'Escape':
        this.navService.navigateOut();
        break;
    }
  }
}
