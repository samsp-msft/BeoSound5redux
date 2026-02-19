import { BeoModuleProvider } from '../module.provider';
import { NavItem } from '../../nav.service';

export class ScenesModuleProvider implements BeoModuleProvider {
  getNavItems(): NavItem[] {
    return [
      { id: 's1', label: 'Relax' },
      { id: 's2', label: 'Party' },
      { id: 's3', label: 'Movie' }
    ];
  }
}
