import { NavItem } from '../nav.service';

export interface BeoModuleProvider {
  getNavItems(): NavItem[] | Promise<NavItem[]>;
}
