import { Injectable, signal, computed } from '@angular/core';

export interface NavItem {
  id: string;
  label: string;
  children?: NavItem[];
}

@Injectable({
  providedIn: 'root'
})
export class NavService {
  public rootItems: NavItem[] = [
    { id: 'playing', label: 'Playing' },
    {
      id: 'music',
      label: 'Music',
      children: [
        { id: 'm-artists', label: 'Artists', children: [{ id: 'a1', label: 'Pink Floyd' }, { id: 'a2', label: 'Daft Punk' }] },
        { id: 'm-albums', label: 'Albums', children: [{ id: 'al1', label: 'Dark Side of the Moon' }, { id: 'al2', label: 'Discovery' }] },
        { id: 'm-genres', label: 'Genres', children: [{ id: 'g1', label: 'Rock' }, { id: 'g2', label: 'Electronic' }] }
      ]
    },
    {
      id: 'tv',
      label: 'TV',
      children: [
        {
          id: 'netflix',
          label: 'Netflix',
          children: [
            { id: 'st', label: 'Stranger Things', children: [{ id: 'st1', label: 'S1:E1' }, { id: 'st2', label: 'S1:E2' }] },
            { id: 'crown', label: 'The Crown', children: [{ id: 'c1', label: 'S1:E1' }] }
          ]
        },
        { id: 'disney', label: 'Disney+', children: [] },
        { id: 'prime', label: 'Prime Video', children: [] }
      ]
    },
    { id: 'scenes', label: 'Scenes', children: [{ id: 's1', label: 'Relax' }, { id: 's2', label: 'Party' }, { id: 's3', label: 'Movie' }] },
    { id: 'system', label: 'System' }
  ];

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
    // Initialize stack with children of the default root selection
    this.updateStackFromRoot();
  }

  private updateStackFromRoot() {
    const rootItem = this.rootItems[this.rootSelectionIdx()];
    if (rootItem.children) {
      this.stack.set([rootItem.children]);
      this.selectionStack.set([0]);
    } else {
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
