import { BeoModuleProvider } from '../module.provider';
import { NavItem } from '../../nav.service';

export class PlayingModuleProvider implements BeoModuleProvider {
  getNavItems(): NavItem[] {
    return [];
  }
}
