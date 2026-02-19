import { BeoModuleProvider } from '../module.provider';
import { NavItem } from '../../nav.service';

export class TvModuleProvider implements BeoModuleProvider {
  getNavItems(): NavItem[] {
    return [
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
    ];
  }
}
