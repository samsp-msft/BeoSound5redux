import { Component, computed, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NavService, NavItem } from './nav.service';

@Component({
  selector: 'app-nav-stack',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="nav-container">
      <!-- Background curve -->
      <svg class="nav-svg" viewBox="0 0 1024 768">
        <!-- Root Menu Orbital Arc (Flipped horizontally to bow towards items) -->
        <!--<path [attr.d]="menuArcPath()" fill="none" stroke="rgba(255,255,255,0.15)" stroke-width="1.5" />-->
      </svg>

      <!-- Decorative Root Arc -->
      <svg width="1024" height="768" style="position: absolute; z-index: 90; pointer-events: none; transition: none; display: block; opacity: 1; transform: translateX(0px);">
          <defs>
              <linearGradient id="gradient" gradientTransform="rotate(90)">
                  <stop offset="0%" stop-color="rgba(102,153,255,0)"></stop>
                  <stop offset="5%" stop-color="rgba(102,153,255,1)"></stop>
                  <stop offset="95%" stop-color="rgba(0,255,204,1)"></stop>
                  <stop offset="100%" stop-color="rgba(0,255,204,0)"></stop>
              </linearGradient>
          </defs>
          <path id="mainArc" fill="none" stroke="url(#gradient)" stroke-width="3" stroke-linecap="round" d="M 219.81614543321257 12.393406584087984 A 1000 1000 0 0 0 219.81614543321268 761.6065934159122"></path>
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
             [style.left.px]="i * 40"
             [style.opacity]="1 - (breadcrumbs().length - 1 - i) * 0.2">
          {{ level.label }}
        </div>
      </div>

      <!-- Active Arc Container (Sub-navigation) -->
      <div class="active-arc-container" *ngIf="activeViewType() !== 'NOW_PLAYING'">
        <div *ngFor="let v of virtualizedItems()"
             class="arc-item"
             [class.selected]="v.index === activeSelection()"
             [style.transform]="getItemTransform(v.index)">
          {{ v.item.label }}
        </div>
      </div>

      <!-- Now Playing View -->
      <div class="now-playing-view" *ngIf="activeViewType() === 'NOW_PLAYING'">
        <div class="np-artwork-container" *ngIf="nowPlayingPortrait()">
          <img [src]="nowPlayingPortrait()" class="np-portrait-art" alt="">
          <div class="np-artwork-shadow"></div>
        </div>
        
        <div class="now-playing-content" *ngIf="nowPlayingItem() as item">
          <div class="np-metadata">
            <div class="np-title">{{ item.label }}</div>
            <div class="np-subtext">{{ item.subText }}</div>
            <div class="np-description" *ngIf="item.description">{{ item.description }}</div>
            <div class="np-app" *ngIf="activeLevelData()?.currentApp">{{ activeLevelData()?.currentApp }}</div>
          </div>
        </div>
      </div>

      <!-- Selection Preview (Absolute positioned) -->
      <div class="selection-preview" *ngIf="selectedItemThumbnail() && activeViewType() !== 'NOW_PLAYING'">
        <img [src]="selectedItemThumbnail()" alt="">
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
      font-family: 'Monserrat', sans-serif;
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
      right: 0; 
      top: 0;
      width: 300px;
      height: 40px;
      line-height: 40px;
      margin-top: -20px;
      text-align: right;
      font-size: 15px;
      color: #888888;
      transition: all 0.3s ease;
      white-space: nowrap;
      text-transform: uppercase;
      letter-spacing: 2px;
      font-weight: 200;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .root-item.selected {
      color: #fff;
      font-size: 16px;
      font-weight: 200;
      opacity: 1;
    }

    .breadcrumbs {
      position: absolute;
      top: 50%;
      left: 200px; /* Offset from the root menu */
      //transform: translateY(-50%);
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
      width: 300px;
      height: 50px;
      line-height: 60px;
      margin-top: -30px; 
      text-align: right;
      font-size: 16px;
      color: rgba(255, 255, 255, 0.3);
      transition: all 0.4s cubic-bezier(0.19, 1, 0.22, 1);
      white-space: nowrap;
      pointer-events: none;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .arc-item.selected {
      color: #fff;
      font-size: 18px;
      letter-spacing: 1px;
      text-shadow: 0 0 6px rgba(255, 255, 255, 0.5);
    }

    .selection-preview {
      position: absolute;
      left: 300px;
      top: 50px;
      width: 200px;
      height: 300px;
      z-index: 5;
      border-radius: 4px;
      overflow: hidden;
      box-shadow: 0 20px 50px rgba(0,0,0,0.8);
      background: #111;
      transition: all 0.5s ease;
    }

    .selection-preview img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }

    /* Now Playing Redesign */
    .now-playing-view {
      position: absolute;
      left: 250px;
      top: 50%;
      width: 600px;
      height: 550px;
      transform: translateY(-50%);
      display: flex;
      align-items: center;
      gap: 50px;
      z-index: 100;
      animation: fadeIn 0.8s ease-out;
    }

    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(-48%); }
      to { opacity: 1; transform: translateY(-50%); }
    }

    .np-artwork-container {
      position: relative;
      flex-shrink: 0;
      width: 360px;
      height: 540px;
      box-shadow: 0 30px 60px rgba(0,0,0,0.8);
      border-radius: 4px;
      overflow: hidden;
    }

    .np-portrait-art {
      width: 100%;
      height: 100%;
      object-fit: cover;
      display: block;
    }

    .np-artwork-shadow {
      position: absolute;
      inset: 0;
      box-shadow: inset 0 0 100px rgba(0,0,0,0.4);
      pointer-events: none;
    }

    .now-playing-content {
      flex-grow: 1;
      text-align: left;
    }

    .np-metadata {
      max-width: 450px;
    }

    .np-title {
      font-size: 42px;
      font-weight: 200;
      color: #fff;
      margin-bottom: 8px;
      text-transform: uppercase;
      letter-spacing: 3px;
      line-height: 1.1;
    }

    .np-subtext {
      font-size: 18px;
      color: #6699ff; /* Accent color from BeoSound theme */
      font-weight: 200;
      text-transform: uppercase;
      letter-spacing: 2px;
      margin-bottom: 24px;
    }

    .np-description {
      font-size: 15px;
      color: #999;
      line-height: 1.6;
      margin-bottom: 30px;
      font-weight: 300;
      display: -webkit-box;
      -webkit-line-clamp: 6;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }

    .np-app {
      font-size: 12px;
      color: rgba(255, 255, 255, 0.5);
      border: 1px solid rgba(255, 255, 255, 0.2);
      padding: 6px 16px;
      display: inline-block;
      border-radius: 20px;
      text-transform: uppercase;
      letter-spacing: 1px;
    }
  `]
})
export class NavStackComponent {
  private navService = inject(NavService);

  rootItems = this.navService.rootItems;
  rootSelectionIdx = this.navService.rootSelection;
  navStack = this.navService.navStack;
  navStackData = this.navService.navStackData;
  navSelections = this.navService.navSelections;

  private angleStep = 12; 
  private rootAngleStep = 8; 

  activeLevelData = computed(() => {
    const stack = this.navStackData();
    return stack.length > 0 ? stack[stack.length - 1] : null;
  });

  activeViewType = computed(() => {
    return this.activeLevelData()?.viewType || 'ARC_LIST';
  });

  nowPlayingItem = computed(() => {
    const data = this.activeLevelData();
    if (data?.viewType === 'NOW_PLAYING' && data.items.length > 0) {
      return data.items[0];
    }
    return null;
  });

  nowPlayingPortrait = computed(() => {
    const item = this.nowPlayingItem();
    return item?.images?.portrait_large || item?.images?.landscape_large || null;
  });

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

  selectedItemThumbnail = computed(() => {
    const npItem = this.nowPlayingItem();
    if (npItem) {
      return npItem.images?.portrait_large || null;
    }
    
    const items = this.activeLevelItems();
    const idx = this.activeSelection();
    const item = (idx !== -1 && items[idx]) ? items[idx] : null;
    return item?.images?.portrait_small || null;
  });

  virtualizedItems = computed(() => {
    const items = this.activeLevelItems();
    const selectedIdx = this.activeSelection();
    if (selectedIdx === -1) return [];

    const start = Math.max(0, selectedIdx - 6);
    const end = Math.min(items.length, selectedIdx + 7);

    return items.slice(start, end).map((item: NavItem, i: number) => ({ item, index: start + i }));
  });

  menuArcPath = computed(() => {
    const cx = 1184;
    const cy = 384;
    const radius = 260; 
    // Arc on the left side of the circle (centered at 180 degrees)
    const startAngle = (180 - 60) * (Math.PI / 180);
    const endAngle = (180 + 60) * (Math.PI / 180);
    
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
    
    const radius = 1060; // Radius to reach the left side from the right-hand center
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
    const radius = baseRadius; //index === selectedIdx ? baseRadius + 20 : baseRadius;
    const x = Math.cos(rad) * radius;
    const y = Math.sin(rad) * radius;
    
    return `translate(${x}px, ${y}px)`;
  }
}
