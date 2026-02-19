import { InjectionToken } from '@angular/core';
import { BeoModuleProvider } from './module.provider';

export interface BeoModuleConfig {
  id: string;
  label: string;
  load: () => Promise<BeoModuleProvider>;
}

export const BEO_MODULES = new InjectionToken<BeoModuleConfig[]>('BEO_MODULES');
