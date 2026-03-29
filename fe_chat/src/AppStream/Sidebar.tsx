import CoinList from "./CoinList";
import LeveragePanel from "./LeveragePanel";

interface SidebarProps {
  collapsed: boolean;
  onCoinClick: (coin: string) => void;
}

export default function Sidebar({ collapsed, onCoinClick }: SidebarProps) {
  return (
    <aside className={`sidebar ${collapsed ? "collapsed" : ""}`}>
      <div className="sidebar-content">
        <LeveragePanel />
        <CoinList onCoinClick={onCoinClick} />
      </div>
    </aside>
  );
}
