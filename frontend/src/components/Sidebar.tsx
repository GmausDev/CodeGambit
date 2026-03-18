import { NavLink } from 'react-router-dom';
import clsx from 'clsx';

const links = [
  { to: '/', label: 'Dashboard', icon: '\u265F' },
  { to: '/challenges', label: 'Challenges', icon: '\u265E' },
  { to: '/calibration', label: 'Calibration', icon: '\u265C' },
];

interface SidebarProps {
  open?: boolean;
  onClose?: () => void;
}

export default function Sidebar({ open, onClose }: SidebarProps) {
  return (
    <>
      {/* Mobile overlay */}
      {open && (
        <div
          className="fixed inset-0 z-30 bg-black/60 backdrop-blur-sm lg:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}
      <aside
        aria-label="Navigation"
        className={clsx(
          'fixed inset-y-0 left-0 z-40 w-64 bg-gray-950 border-r border-gray-800 flex flex-col transition-transform duration-200 ease-in-out lg:translate-x-0 lg:static lg:z-auto',
          open ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="p-6 border-b border-gray-800">
          <h1 className="text-xl font-bold text-brand-500 font-mono tracking-tight">
            CodeGambit
          </h1>
          <p className="text-xs text-gray-500 mt-1 italic">
            Sacrifice comfort. Gain depth.
          </p>
        </div>
        <nav className="flex-1 p-4 space-y-1">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.to === '/'}
              aria-label={link.label}
              onClick={onClose}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors',
                  isActive
                    ? 'bg-brand-700/20 text-brand-400 border-l-2 border-brand-500'
                    : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/50 border-l-2 border-transparent'
                )
              }
            >
              <span className="text-lg" aria-hidden="true">{link.icon}</span>
              {link.label}
            </NavLink>
          ))}
        </nav>
        <div className="p-4 border-t border-gray-800">
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <span aria-hidden="true">{'\u265A'}</span>
            <span>ELO: <span className="text-brand-400 font-mono font-medium">--</span></span>
          </div>
        </div>
      </aside>
    </>
  );
}
