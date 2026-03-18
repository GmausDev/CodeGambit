import { NavLink } from 'react-router-dom';
import clsx from 'clsx';

const links = [
  { to: '/', label: 'Dashboard', icon: '♟' },
  { to: '/challenges', label: 'Challenges', icon: '♞' },
  { to: '/calibration', label: 'Calibration', icon: '♜' },
];

export default function Sidebar() {
  return (
    <aside className="w-64 bg-gray-950 border-r border-gray-800 flex flex-col">
      <div className="p-6 border-b border-gray-800">
        <h1 className="text-xl font-bold text-brand-500 font-mono tracking-tight">
          CodeGambit
        </h1>
        <p className="text-xs text-gray-500 mt-1">Developer Training Platform</p>
      </div>
      <nav className="flex-1 p-4 space-y-1">
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            end={link.to === '/'}
            className={({ isActive }) =>
              clsx(
                'flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors',
                isActive
                  ? 'bg-brand-700/20 text-brand-500'
                  : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/50'
              )
            }
          >
            <span className="text-lg">{link.icon}</span>
            {link.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
