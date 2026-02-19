import { ApplicationConfig, provideBrowserGlobalErrorListeners } from '@angular/core';
import { provideRouter } from '@angular/router';

import { routes } from './app.routes';
import { provideClientHydration, withEventReplay } from '@angular/platform-browser';
import { BEO_MODULES } from './modules/module.config';
import { PlayingModuleProvider } from './modules/playing/playing.provider';
import { MusicModuleProvider } from './modules/music/music.provider';
import { TvModuleProvider } from './modules/tv/tv.provider';
import { ScenesModuleProvider } from './modules/scenes/scenes.provider';
import { SystemModuleProvider } from './modules/system/system.provider';

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideRouter(routes),
    provideClientHydration(withEventReplay()),
    {
      provide: BEO_MODULES,
      useValue: [
        {
          id: 'playing',
          label: 'Playing',
          load: () => Promise.resolve(new PlayingModuleProvider()),
        },
        {
          id: 'music',
          label: 'Music',
          load: () => import('./modules/music/music.provider').then(m => new m.MusicModuleProvider()),
        },
        {
          id: 'tv',
          label: 'TV',
          load: () => import('./modules/tv/tv.provider').then(m => new m.TvModuleProvider()),
        },
        {
          id: 'scenes',
          label: 'Scenes',
          load: () => import('./modules/scenes/scenes.provider').then(m => new m.ScenesModuleProvider()),
        },
        {
          id: 'system',
          label: 'System',
          load: () => import('./modules/system/system.provider').then(m => new m.SystemModuleProvider()),
        },
      ],
    },
  ],
};
