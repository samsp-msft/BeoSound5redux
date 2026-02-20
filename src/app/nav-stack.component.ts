import { Component, computed, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NavService } from './nav.service';

@Component({
  selector: 'app-nav-stack',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="nav-container">
      <!-- Background curve -->
      <svg class="nav-svg" viewBox="0 0 1024 768">
        <!-- Root Menu Orbital Arc (Flipped horizontally to bow towards items) -->
        <path [attr.d]="menuArcPath()" fill="none" stroke="rgba(255,255,255,0.15)" stroke-width="1.5" />
      </svg>

      <!-- Root Menu (Laser Pointer Menu) -->
      <div class="root-menu-container">
        <div *ngFor="let item of rootItems(); let i = index" 
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
      background: radial-gradient(circle at 924px 384px, #111 0%, #000 70%);
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
      left: 1184px; /* Center of the dial on the right */
      top: 384px;
      width: 0;
      height: 0;
      z-index: 50;
    }

    .root-item {
      position: absolute;
      left: 0; 
      top: 0;
      width: 300px;
      height: 40px;
      line-height: 40px;
      margin-top: -20px;
      text-align: left;
      font-size: 16px;
      color: #888888;
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
      left: 200px; /* Offset from the root menu */
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
      left: 1184px; /* Center of the dial on the right */
      top: 384px;
      width: 0;
      height: 0;
      z-index: 50;
    }

    .arc-item {
      position: absolute;
      right: 0; /* Align right side of box to the translation point */
      top: 0;
      width: 600px;
      height: 60px;
      line-height: 60px;
      margin-top: -30px; 
      text-align: right;
      font-size: 24px;
      color: rgba(255, 255, 255, 0.3);
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

  private angleStep = 10; 
  private rootAngleStep = 8; 

  breadcrumbs = computed(() => {
    const stack = this.navStack();
    const selections = this.navSelections();
    return stack.slice(0, -1).map((level, i) => level[selections[i]]);
  });

  activeLevelItems = computed(() => {
    const stack = this.navStack();
    const items = stack.length > 0 ? stack[stack.length - 1] : [];
    console.log('NavStackComponent: Rendering', items.length, 'items at stack level', stack.length);
    return items;
  });

  activeSelection = computed(() => {
    const selections = this.navSelections();
    return selections.length > 0 ? selections[selections.length - 1] : -1;
  });

  menuArcPath = computed(() => {
    const cx = 1184;
    const cy = 384;
    const radius = 260; 
    // Arc on the left side of the circle (centered at 180 degrees)
    const startAngle = (180 - 45) * (Math.PI / 180);
    const endAngle = (180 + 45) * (Math.PI / 180);
    
    const x1 = cx + radius * Math.cos(startAngle);
    const y1 = cy + radius * Math.sin(startAngle);
    const x2 = cx + radius * Math.cos(endAngle);
    const y2 = cy + radius * Math.sin(endAngle);
    
    return `M ${x1} ${y1} A ${radius} ${radius} 0 0 1 ${x2} ${y2}`;
  });

  getRootItemTransform(index: number) {
    const items = this.rootItems();
    const middleIndex = (items.length - 1) / 2;
    // Reverse the visual order: index 0 (Playing) at bottom, last index (System) at top
    const reversedIndex = (items.length - 1) - index;
    const relativeIdx = reversedIndex - middleIndex;
    const angle = 180 + (relativeIdx * 6); // Fixed angle based on position in list
    const rad = angle * Math.PI / 180;
    
    const radius = 1144; // Radius to reach the left side from the right-hand center
    const x = Math.cos(rad) * radius;
    const y = Math.sin(rad) * radius;
    
    return `translate(${x}px, ${y}px)`;
  }

  getItemTransform(index: number) {
    const items = this.activeLevelItems();
    const selectedIdx = this.activeSelection();
    
    // Reverse visual order for items as well
    const reversedIndex = (items.length - 1) - index;
    const reversedSelectedIdx = (items.length - 1) - selectedIdx;
    
    const relativeIdx = reversedIndex - reversedSelectedIdx; 
    const angle = 180 + (relativeIdx * this.angleStep);
    const rad = angle * Math.PI / 180;
    
    const baseRadius = 320; // Moved closer to the dial
    const radius = index === selectedIdx ? baseRadius + 20 : baseRadius;
    const x = Math.cos(rad) * radius;
    const y = Math.sin(rad) * radius;
    
    return `translate(${x}px, ${y}px)`;
  }
}
