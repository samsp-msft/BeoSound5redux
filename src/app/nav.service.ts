import { Injectable, signal, computed, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';

export interface NavItem {
  id: string;
  label: string;
  subText?: string;
  thumbnail?: string;
  template?: string;
  childrenLink?: string;
  actionLink?: string;
}

export interface BrowseResponse {
    title: string;
    viewType: string;
    items: NavItem[];
}

@Injectable({
  providedIn: 'root'
})
export class NavService {
  private http = inject(HttpClient);
  private backendUrl = 'http://localhost:5001';

  private rootItemsSignal = signal<NavItem[]>([]);
  public readonly rootItems = this.rootItemsSignal.asReadonly();
  
  // The index of the selected item in the root menu (left side)
  private rootSelectionIdx = signal<number>(1); // Default to 'Music'

  // The stack of current navigation levels *excluding* the root.
  private stack = signal<NavItem[][]>([]);
  
  // Selection index for each level in the stack.
  private selectionStack = signal<number[]>([]);

  public readonly rootSelection = this.rootSelectionIdx.asReadonly();
  public readonly navStack = this.stack.asReadonly();
  public readonly navSelections = this.selectionStack.asReadonly();

  constructor() {
    this.initialize();
  }

  private async initialize() {
    console.log('NavService: Initializing from Python Engine...');
    try {
        const roots = await firstValueFrom(this.http.get<NavItem[]>(`${this.backendUrl}/roots`));
        this.rootItemsSignal.set(roots);
        console.log('NavService: Root items loaded:', roots.map(i => i.label));
        await this.updateStackFromRoot();
    } catch (error) {
        console.error('NavService: Failed to load roots:', error);
    }
  }

  private async updateStackFromRoot() {
    const rootIdx = this.rootSelectionIdx();
    const rootItem = this.rootItems()[rootIdx];
    
    if (!rootItem || !rootItem.childrenLink) {
        this.stack.set([]);
        this.selectionStack.set([]);
        return;
    }

    try {
        console.log('NavService: Fetching level from:', rootItem.childrenLink);
        const response = await firstValueFrom(this.http.get<BrowseResponse>(`${this.backendUrl}${rootItem.childrenLink}`));
        this.stack.set([response.items]);
        this.selectionStack.set([0]);
    } catch (error) {
        console.error('NavService: Error updating stack from root:', error);
    }
  }

  setRootSelection(index: number) {
    if (index >= 0 && index < this.rootItems().length) {
      this.rootSelectionIdx.set(index);
      this.updateStackFromRoot();
    }
  }

  moveRootSelection(delta: number) {
    let next = this.rootSelectionIdx() + delta;
    if (next < 0) next = 0;
    if (next >= this.rootItems().length) next = this.rootItems().length - 1;
    this.setRootSelection(next);
  }

  moveSelection(delta: number) {
    const currentStack = this.stack();
    if (currentStack.length === 0) return;

    const currentSelections = this.selectionStack();
    const activeLevel = currentStack.length - 1;
    const activeItems = currentStack[activeLevel];
    const currentIdx = currentSelections[activeLevel];

    let nextIdx = currentIdx + delta;
    if (nextIdx < 0) nextIdx = 0;
    if (nextIdx >= activeItems.length) nextIdx = activeItems.length - 1;

    if (nextIdx !== currentIdx) {
      const newSelections = [...currentSelections];
      newSelections[activeLevel] = nextIdx;
      this.selectionStack.set(newSelections);
    }
  }

  async navigateIn() {
    const currentStack = this.stack();
    if (currentStack.length === 0) return;

    const currentSelections = this.selectionStack();
    const activeLevel = currentStack.length - 1;
    const activeIdx = currentSelections[activeLevel];
    const selectedItem = currentStack[activeLevel][activeIdx];

    if (selectedItem.actionLink) {
        console.log('NavService: Executing action:', selectedItem.actionLink);
        try {
            await firstValueFrom(this.http.post(`${this.backendUrl}${selectedItem.actionLink}`, {}));
        } catch (error) {
            console.error('NavService: Action failed:', error);
        }
        return;
    }

    if (selectedItem.childrenLink) {
        try {
            console.log('NavService: Navigating into:', selectedItem.childrenLink);
            const response = await firstValueFrom(this.http.get<BrowseResponse>(`${this.backendUrl}${selectedItem.childrenLink}`));
            this.stack.set([...currentStack, response.items].slice(-5));
            this.selectionStack.set([...currentSelections, 0]);
        } catch (error) {
            console.error('NavService: Navigation failed:', error);
        }
    }
  }

  navigateOut() {
    const currentStack = this.stack();
    if (currentStack.length > 1) {
      this.stack.set(currentStack.slice(0, -1));
      this.selectionStack.set(this.selectionStack().slice(0, -1));
    }
  }
}
