import type {
  ISeriesPrimitive,
  SeriesAttachedParameter,
  ISeriesApi,
  SeriesType,
  Time,
  IChartApiBase,
  IPrimitivePaneView,
  IPrimitivePaneRenderer,
  PrimitivePaneViewZOrder,
} from "lightweight-charts";

// ─── Box Primitive (Order Blocks & FVGs) ──────────────────────────────────────
// Draws a filled rectangle between two price levels over a time range.

export interface BoxOptions {
  timeFrom: Time;
  timeTo: Time;
  priceHigh: number;
  priceLow: number;
  fillColor: string;    // e.g. 'rgba(34,197,94,0.12)'
  borderColor: string;
  lineWidth?: number;
  lineDash?: number[];  // e.g. [4, 4] for dashed border
  label?: string;
}

class BoxPaneRenderer implements IPrimitivePaneRenderer {
  private _opts: BoxOptions;
  private _chart: IChartApiBase<Time>;
  private _series: ISeriesApi<SeriesType>;

  constructor(
    opts: BoxOptions,
    chart: IChartApiBase<Time>,
    series: ISeriesApi<SeriesType>
  ) {
    this._opts = opts;
    this._chart = chart;
    this._series = series;
  }

  draw(target: any): void {
    target.useBitmapCoordinateSpace(
      (scope: {
        context: CanvasRenderingContext2D;
        horizontalPixelRatio: number;
        verticalPixelRatio: number;
      }) => {
        const ctx = scope.context;
        const hr = scope.horizontalPixelRatio;
        const vr = scope.verticalPixelRatio;

        const x1 = this._chart.timeScale().timeToCoordinate(this._opts.timeFrom);
        const x2 = this._chart.timeScale().timeToCoordinate(this._opts.timeTo);
        const y1 = this._series.priceToCoordinate(this._opts.priceHigh);
        const y2 = this._series.priceToCoordinate(this._opts.priceLow);

        if (x1 === null || x2 === null || y1 === null || y2 === null) return;

        const rx1 = Math.round(x1 * hr);
        const rx2 = Math.round(x2 * hr);
        const ry1 = Math.round(y1 * vr);
        const ry2 = Math.round(y2 * vr);
        const rw = rx2 - rx1;
        const rh = ry2 - ry1;

        // Filled area
        ctx.fillStyle = this._opts.fillColor;
        ctx.fillRect(rx1, ry1, rw, rh);

        // Border
        ctx.strokeStyle = this._opts.borderColor;
        ctx.lineWidth = (this._opts.lineWidth ?? 1) * vr;
        if (this._opts.lineDash) {
          ctx.setLineDash(this._opts.lineDash.map((d) => d * vr));
        } else {
          ctx.setLineDash([]);
        }
        ctx.strokeRect(rx1, ry1, rw, rh);
        ctx.setLineDash([]);

        // Label inside top-left of box
        if (this._opts.label) {
          ctx.font = `bold ${Math.round(9.5 * vr)}px 'SF Mono', Consolas, monospace`;
          ctx.fillStyle = this._opts.borderColor;
          ctx.textAlign = "left";
          ctx.textBaseline = "top";
          ctx.fillText(
            this._opts.label,
            rx1 + Math.round(4 * hr),
            ry1 + Math.round(3 * vr)
          );
        }
      }
    );
  }
}

class BoxPaneView implements IPrimitivePaneView {
  private _renderer: BoxPaneRenderer;

  constructor(
    opts: BoxOptions,
    chart: IChartApiBase<Time>,
    series: ISeriesApi<SeriesType>
  ) {
    this._renderer = new BoxPaneRenderer(opts, chart, series);
  }

  zOrder(): PrimitivePaneViewZOrder {
    return "bottom"; // render behind candles
  }

  renderer(): IPrimitivePaneRenderer {
    return this._renderer;
  }
}

export class BoxPrimitive implements ISeriesPrimitive<Time> {
  private _opts: BoxOptions;
  private _chart: IChartApiBase<Time> | null = null;
  private _series: ISeriesApi<SeriesType> | null = null;
  private _views: BoxPaneView[] = [];

  constructor(opts: BoxOptions) {
    this._opts = opts;
  }

  attached(params: SeriesAttachedParameter<Time>): void {
    this._chart = params.chart;
    this._series = params.series;
    this._views = [new BoxPaneView(this._opts, this._chart, this._series)];
  }

  detached(): void {
    this._chart = null;
    this._series = null;
    this._views = [];
  }

  paneViews(): readonly IPrimitivePaneView[] {
    return this._views;
  }

  updateAllViews(): void {}
}

// ─── Horizontal Line Primitive (BOS / CHoCH) ─────────────────────────────────
// Draws a labeled horizontal line from a start time to the right edge of the chart.

export interface HLineOptions {
  timeFrom: Time;
  price: number;
  color: string;
  lineWidth?: number;
  lineDash?: number[];
  label?: string;
  labelColor?: string;
}

class HLinePaneRenderer implements IPrimitivePaneRenderer {
  private _opts: HLineOptions;
  private _chart: IChartApiBase<Time>;
  private _series: ISeriesApi<SeriesType>;

  constructor(
    opts: HLineOptions,
    chart: IChartApiBase<Time>,
    series: ISeriesApi<SeriesType>
  ) {
    this._opts = opts;
    this._chart = chart;
    this._series = series;
  }

  draw(target: any): void {
    target.useBitmapCoordinateSpace(
      (scope: {
        context: CanvasRenderingContext2D;
        horizontalPixelRatio: number;
        verticalPixelRatio: number;
        bitmapSize: { width: number; height: number };
      }) => {
        const ctx = scope.context;
        const hr = scope.horizontalPixelRatio;
        const vr = scope.verticalPixelRatio;

        const x1 = this._chart.timeScale().timeToCoordinate(this._opts.timeFrom);
        const y = this._series.priceToCoordinate(this._opts.price);

        if (x1 === null || y === null) return;

        const rx1 = Math.round(x1 * hr);
        const ry = Math.round(y * vr);
        const rx2 = scope.bitmapSize.width; // full width to right edge

        ctx.strokeStyle = this._opts.color;
        ctx.lineWidth = (this._opts.lineWidth ?? 1.5) * vr;
        if (this._opts.lineDash) {
          ctx.setLineDash(this._opts.lineDash.map((d) => d * vr));
        }

        ctx.beginPath();
        ctx.moveTo(rx1, ry);
        ctx.lineTo(rx2, ry);
        ctx.stroke();
        ctx.setLineDash([]);

        // Label at start of line
        if (this._opts.label) {
          const pad = Math.round(4 * hr);
          ctx.font = `bold ${Math.round(9.5 * vr)}px 'SF Mono', Consolas, monospace`;
          ctx.fillStyle = this._opts.labelColor ?? this._opts.color;
          ctx.textAlign = "left";
          ctx.textBaseline = "bottom";
          ctx.fillText(this._opts.label, rx1 + pad, ry - Math.round(2 * vr));
        }
      }
    );
  }
}

class HLinePaneView implements IPrimitivePaneView {
  private _renderer: HLinePaneRenderer;

  constructor(
    opts: HLineOptions,
    chart: IChartApiBase<Time>,
    series: ISeriesApi<SeriesType>
  ) {
    this._renderer = new HLinePaneRenderer(opts, chart, series);
  }

  zOrder(): PrimitivePaneViewZOrder {
    return "normal";
  }

  renderer(): IPrimitivePaneRenderer {
    return this._renderer;
  }
}

export class HLinePrimitive implements ISeriesPrimitive<Time> {
  private _opts: HLineOptions;
  private _chart: IChartApiBase<Time> | null = null;
  private _series: ISeriesApi<SeriesType> | null = null;
  private _views: HLinePaneView[] = [];

  constructor(opts: HLineOptions) {
    this._opts = opts;
  }

  attached(params: SeriesAttachedParameter<Time>): void {
    this._chart = params.chart;
    this._series = params.series;
    this._views = [new HLinePaneView(this._opts, this._chart, this._series)];
  }

  detached(): void {
    this._chart = null;
    this._series = null;
    this._views = [];
  }

  paneViews(): readonly IPrimitivePaneView[] {
    return this._views;
  }

  updateAllViews(): void {}
}
