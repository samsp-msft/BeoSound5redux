import { BeoModuleProvider } from '../module.provider';
import { NavItem } from '../../nav.service';

export class SystemModuleProvider implements BeoModuleProvider {
  getNavItems(): NavItem[] {
    return [];
  }
}
