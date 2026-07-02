export interface StockRankItem {
    rank: number;
    stock_code: string;
    stock_name: string;
    price: number;
    change_rate: number;
    volume?: number;
    trade_value?: number;
    net_buy_qty?: number;
    net_buy_amount?: number;
}

export interface MinuteChartItem {
    stock_code: string;
    trade_date: string;
    trade_time: string;
    open_price: number;
    high_price: number;
    low_price: number;
    close_price: number;
    volume: number;
    cumul_amount: number;
}

export interface OHLCVItem {
    date: string;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
    amount: number;
    change_sign: string;
    change_val: number;
}

export interface CurrentPriceResponse {
    current: number;
    open: number;
    high: number;
    low: number;
    change_val: number;
    change_rate: number;
    volume: number;
    market_cap: number;
    per: number;
    pbr: number;
    foreign_ratio: number;
}

export interface AccountSummary {
    deposit: number;
    total_eval: number;
    total_profit: number;
}

export interface HoldingStock {
    stock_code: string;
    stock_name: string;
    quantity: number;
    avg_price: number;
    current_price: number;
    profit_rate: number;
}

export interface AccountBalanceResponse {
    summary: AccountSummary;
    stocks: HoldingStock[];
}

export interface OrderExecution {
    order_no: string;
    stock_code: string;
    stock_name: string;
    side: string;
    order_qty: number;
    filled_qty: number;
    avg_price: number;
    total_amount: number;
}

export interface OrderbookItem {
    ask_price: string;
    bid_price: string;
    ask_rsvp: string;
    bid_rsvp: string;
}

export interface OrderbookResponse {
    output1: OrderbookItem[];
    output2: {
        antc_cntg_prce: string;
        antc_cntg_vrss: string;
        antc_cntg_ctrt: string;
    };
}

export interface InvestorItem {
    stck_bsop_date: string;
    prsn_ntby_qty: string;
    frgn_ntby_qty: string;
    orgn_ntby_qty: string;
}
