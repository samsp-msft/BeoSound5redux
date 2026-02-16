import { Component, computed, inject, HostListener } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NavService } from './nav.service';

@Component({
  selector: 'app-nav-stack',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="nav-container" (wheel)="onWheel($event)">
      <!-- Background curve -->
      <svg class="nav-svg" viewBox="0 0 1024 768">
        <!-- Root Menu Orbital Arc (Flipped horizontally to bow towards items) -->
        <path [attr.d]="menuArcPath()" fill="none" stroke="rgba(255,255,255,0.15)" stroke-width="1.5" />
      </svg>

      <!-- Root Menu (Laser Pointer Menu) -->
      <div class="root-menu-container">
        <div *ngFor="let item of rootItems; let i = index" 
             class="root-item"
             [class.selected]="i === rootSelectionIdx()"
             [style.transform]="getRootItemTransform(i)">
          {{ item.label }}
        </div>
      </div>

      <!-- Breadcrumbs (Sub-navigation history) -->
      <div class="breadcrumbs">
        <div *ngFor="let level of breadcrumbs(); let i = index" 
             class="breadcrumb-item"
             [style.left.px]="i * 60"
             [style.opacity]="1 - (breadcrumbs().length - 1 - i) * 0.2">
          {{ level.label }}
        </div>
      </div>

      <!-- Active Arc Container (Sub-navigation) -->
      <div class="active-arc-container">
        <div *ngFor="let item of activeLevelItems(); let i = index"
             class="arc-item"
             [class.selected]="i === activeSelection()"
             [style.transform]="getItemTransform(i)">
          {{ item.label }}
        </div>
      </div>
    </div>
  `,
  styles: [`
    .nav-container {
      position: relative;
      width: 1024px;
      height: 768px;
      overflow: hidden;
      background: #000;
      background: radial-gradient(circle at 1136px 384px, #111 0%, #000 70%);
      font-family: 'Beo', sans-serif;
    }

    .nav-svg {
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      pointer-events: none;
    }

    .root-menu-container {
      position: absolute;
      left: 1136px;
      top: 384px;
      width: 0;
      height: 0;
      z-index: 50;
    }

    .root-item {
      position: absolute;
      right: 950px; 
      width: 150px;
      text-align: left;
      font-size: 16px;
      color: #888888;
      transform-origin: 1050px center;
      transition: all 0.3s ease;
      white-space: nowrap;
      text-transform: uppercase;
      letter-spacing: 2px;
    }

    .root-item.selected {
      color: #fff;
      font-size: 20px;
      font-weight: 600;
      opacity: 1;
    }

    .breadcrumbs {
      position: absolute;
      top: 50%;
      left: 200px; 
      transform: translateY(-50%);
      display: flex;
      flex-direction: column;
      gap: 30px;
      z-index: 10;
    }

    .breadcrumb-item {
      position: relative;
      font-size: 16px;
      color: #fff;
      text-transform: uppercase;
      letter-spacing: 2px;
      white-space: nowrap;
      transition: all 0.5s cubic-bezier(0.19, 1, 0.22, 1);
    }

    .breadcrumb-item::after {
      content: '';
      position: absolute;
      bottom: -5px;
      left: 0;
      width: 30px;
      height: 1px;
      background: rgba(255, 255, 255, 0.3);
    }

    .active-arc-container {
      position: absolute;
      left: 1136px;
      top: 384px;
      width: 0;
      height: 0;
      z-index: 50;
    }

    .arc-item {
      position: absolute;
      right: 0;
      top: 0;
      width: 400px;
      height: 60px;
      line-height: 60px;
      margin-top: -30px; 
      text-align: right;
      font-size: 24px;
      color: rgba(255, 255, 255, 0.3);
      transform-origin: 400px center;
      transition: all 0.4s cubic-bezier(0.19, 1, 0.22, 1);
      white-space: nowrap;
      pointer-events: none;
      text-transform: uppercase;
      letter-spacing: 1px;
    }

    .arc-item.selected {
      color: #fff;
      font-size: 30px;
      letter-spacing: 3px;
      text-shadow: 0 0 20px rgba(255, 255, 255, 0.5);
    }
  `]
})
export class NavStackComponent {
  private navService = inject(NavService);

  rootItems = this.navService.rootItems;
  rootSelectionIdx = this.navService.rootSelection;
  navStack = this.navService.navStack;
  navSelections = this.navService.navSelections;

  private angleStep = 15; // Degrees for sub-menu
  private rootAngleStep = 5; // Degrees for root menu

  breadcrumbs = computed(() => {
    const stack = this.navStack();
    const selections = this.navSelections();
    return stack.slice(0, -1).map((level, i) => level[selections[i]]);
  });

  activeLevelItems = computed(() => {
    const stack = this.navStack();
    return stack.length > 0 ? stack[stack.length - 1] : [];
  });

  activeSelection = computed(() => {
    const selections = this.navSelections();
    return selections.length > 0 ? selections[selections.length - 1] : -1;
  });

  menuArcPath = computed(() => {
    // Flipped horizontally: Center is now to the LEFT of the items.
    const cx = -900;
    const cy = 384;
    const radius = 1006; // Places arc at X=106
    const startAngle = -15 * (Math.PI / 180);
    const endAngle = 15 * (Math.PI / 180);
    
    const x1 = cx + radius * Math.cos(startAngle);
    const y1 = cy + radius * Math.sin(startAngle);
    const x2 = cx + radius * Math.cos(endAngle);
    const y2 = cy + radius * Math.sin(endAngle);
    
    return `M ${x1} ${y1} A ${radius} ${radius} 0 0 1 ${x2} ${y2}`;
  });

  getRootItemTransform(index: number) {
    const middleIndex = (this.rootItems.length - 1) / 2;
    const angle = (index - middleIndex) * -this.rootAngleStep;
    return `rotate(${angle}deg)`;
  }

  getItemTransform(index: number) {
    const selectedIdx = this.activeSelection();
    const relativeIdx = selectedIdx - index; 
    const angle = relativeIdx * this.angleStep;
    const radius = index === selectedIdx ? 320 : 280;
    return `rotate(${angle}deg) translateX(-${radius}px)`;
  }

  onWheel(event: WheelEvent) {
    if (Math.abs(event.deltaY) > 5) {
      this.navService.moveSelection(event.deltaY > 0 ? 1 : -1);
    }
    event.preventDefault();
  }

  @HostListener('window:keydown', ['$event'])
  onKeyDown(event: KeyboardEvent) {
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
      case 'BackSpace':
      case 'Escape':
        this.navService.navigateOut();
        break;
    }
  }
}
