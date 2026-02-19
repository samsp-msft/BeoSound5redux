import { BeoModuleProvider } from '../module.provider';
import { NavItem } from '../../nav.service';

export class MusicModuleProvider implements BeoModuleProvider {
  getNavItems(): NavItem[] {
    return [
      { id: 'm-artists', label: 'Artists', children: [{ id: 'a1', label: 'Pink Floyd' }, { id: 'a2', label: 'Daft Punk' }] },
      { id: 'm-albums', label: 'Albums', children: [{ id: 'al1', label: 'Dark Side of the Moon' }, { id: 'al2', label: 'Discovery' }] },
      { id: 'm-genres', label: 'Genres', children: [{ id: 'g1', label: 'Rock' }, { id: 'g2', label: 'Electronic' }] }
    ];
  }
}
