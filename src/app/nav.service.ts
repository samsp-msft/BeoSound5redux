import { Injectable, signal, computed, inject } from '@angular/core';
import { BEO_MODULES, BeoModuleConfig } from './modules/module.config';

export interface NavItem {
  id: string;
  label: string;
  children?: NavItem[];
}

@Injectable({
  providedIn: 'root'
})
export class NavService {
  private modules: BeoModuleConfig[] = inject(BEO_MODULES);
  public rootItems: NavItem[] = [];

  // The index of the selected item in the root menu (left side)
  private rootSelectionIdx = signal<number>(1); // Default to 'Music'

  // The stack of current navigation levels *excluding* the root.
  // When at the very beginning, this might be empty or contain the children of the root selection.
  private stack = signal<NavItem[][]>([]);
  
  // Selection index for each level in the stack.
  private selectionStack = signal<number[]>([]);

  public readonly rootSelection = this.rootSelectionIdx.asReadonly();
  public readonly navStack = this.stack.asReadonly();
  public readonly navSelections = this.selectionStack.asReadonly();

  constructor() {
    this.rootItems = this.modules.map(m => ({ id: m.id, label: m.label }));
    // Initialize stack with children of the default root selection
    this.updateStackFromRoot();
  }

  private async updateStackFromRoot() {
    const rootModuleConfig = this.modules[this.rootSelectionIdx()];
    const provider = await rootModuleConfig.load();
    const children = await provider.getNavItems();
    
    if (children && children.length > 0) {
      this.rootItems[this.rootSelectionIdx()].children = children;
      this.stack.set([children]);
      this.selectionStack.set([0]);
    } else {
      this.rootItems[this.rootSelectionIdx()].children = [];
      this.stack.set([]);
      this.selectionStack.set([]);
    }
  }

  setRootSelection(index: number) {
    if (index >= 0 && index < this.rootItems.length) {
      this.rootSelectionIdx.set(index);
      this.updateStackFromRoot();
    }
  }

  moveRootSelection(delta: number) {
    let next = this.rootSelectionIdx() + delta;
    if (next < 0) next = 0;
    if (next >= this.rootItems.length) next = this.rootItems.length - 1;
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

  navigateIn() {
    const currentStack = this.stack();
    if (currentStack.length === 0) return;

    const currentSelections = this.selectionStack();
    const activeLevel = currentStack.length - 1;
    const activeIdx = currentSelections[activeLevel];
    const selectedItem = currentStack[activeLevel][activeIdx];

    if (selectedItem.children && selectedItem.children.length > 0) {
      this.stack.set([...currentStack, selectedItem.children].slice(-5));
      this.selectionStack.set([...currentSelections, 0]);
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
