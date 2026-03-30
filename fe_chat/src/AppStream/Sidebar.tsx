import LeveragePanel from "./LeveragePanel";
import CoinList from "./CoinList";

interface Props {
  collapsed: boolean;
  onCoinClick: (coin: string) => void;
  selectedCoin?: string;
}

export default function Sidebar({ onCoinClick, selectedCoin }: Props) {
  return (
    <aside className="sidebar">
      <div className="sidebar-content">
        <LeveragePanel />
        <CoinList onCoinClick={onCoinClick} selectedCoin={selectedCoin} />
      </div>
    </aside>
  );
}
