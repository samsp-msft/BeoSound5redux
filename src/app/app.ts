import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { NavStackComponent } from './nav-stack.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, NavStackComponent],
  template: `
    <div class="beosound-container">
      <div class="dial-obstruction"></div>
      
      <div class="nav-stack">
        <app-nav-stack></app-nav-stack>
      </div>

      <router-outlet />
    </div>
  `,
  styles: [`
    .nav-stack {
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
    }
  `]
})
export class App {
  title = 'beosound5redux';
}
