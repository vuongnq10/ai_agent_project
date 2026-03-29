---
name: chart-analysis
description: Perform a full financial chart analysis for a given symbol and timeframe using Smart Money Concepts. Use when the user asks to analyze a coin, identify trends, find key levels, or determine trade setups.
argument-hint: [symbol] [timeframe]
user-invocable: true
allowed-tools: Read, Grep, Bash
---

# Financial Chart Analysis

Perform a comprehensive Smart Money Concepts (SMC) chart analysis for **$ARGUMENTS**.

# Smart Money Concept (SMC) Trading – Steps & Formulas

# Step 1. Market Data Input

SMC analysis is based on **OHLCV candle data**.

| Symbol | Meaning                 |
| ------ | ----------------------- |
| `O[i]` | Open price of candle i  |
| `H[i]` | High price of candle i  |
| `L[i]` | Low price of candle i   |
| `C[i]` | Close price of candle i |
| `V[i]` | Volume                  |

---

# Step 2. Identify Swing High / Swing Low

Market structure is built from **swing points**.

## Swing High

A candle whose high is greater than surrounding candles.

### Formula

```
SwingHigh(i) = H[i] > H[i-1] AND H[i] > H[i+1]
```

### Strong Swing High (5 candle rule)

```
SwingHigh(i) = H[i] > max(H[i-2], H[i-1], H[i+1], H[i+2])
```

---

## Swing Low

A candle whose low is lower than surrounding candles.

### Formula

```
SwingLow(i) = L[i] < L[i-1] AND L[i] < L[i+1]
```

### Strong Swing Low

```
SwingLow(i) = L[i] < min(L[i-2], L[i-1], L[i+1], L[i+2])
```

---

# Step 3. Market Structure

Market structure is determined by **swing highs and swing lows**.

| Pattern | Meaning     |
| ------- | ----------- |
| HH      | Higher High |
| HL      | Higher Low  |
| LH      | Lower High  |
| LL      | Lower Low   |

---

## Bullish Market Structure

Conditions:

```
HH: H[i] > PreviousSwingHigh
HL: L[i] > PreviousSwingLow
```

Trend rule:

```
BullishTrend =
    HH sequence AND HL sequence
```

Example:

```
HL → HH → HL → HH
```

---

## Bearish Market Structure

Conditions:

```
LL: L[i] < PreviousSwingLow
LH: H[i] < PreviousSwingHigh
```

Trend rule:

```
BearishTrend =
    LL sequence AND LH sequence
```

Example:

```
LH → LL → LH → LL
```

---

# Step 4. Break of Structure (BOS)

BOS confirms **trend continuation**.

## Bullish BOS

Price closes above previous swing high.

```
BullishBOS =
    C[i] > PreviousSwingHigh
```

---

## Bearish BOS

Price closes below previous swing low.

```
BearishBOS =
    C[i] < PreviousSwingLow
```

---

# Step 5. Change of Character (CHoCH)

CHoCH indicates **possible trend reversal**.

## Bullish CHoCH

Occurs when bearish structure breaks upward.

```
BullishCHoCH =
    C[i] > PreviousLowerHigh
```

---

## Bearish CHoCH

Occurs when bullish structure breaks downward.

```
BearishCHoCH =
    C[i] < PreviousHigherLow
```

---

# Step 6. Liquidity

Liquidity exists where many stop losses are placed.

## Types of Liquidity

| Type                | Description       |
| ------------------- | ----------------- |
| Buy-side liquidity  | Above swing highs |
| Sell-side liquidity | Below swing lows  |

---

## Liquidity Sweep

Occurs when price grabs stops.

### Buy-side sweep

```
H[i] > PreviousSwingHigh
AND
C[i] < PreviousSwingHigh
```

### Sell-side sweep

```
L[i] < PreviousSwingLow
AND
C[i] > PreviousSwingLow
```

---

# Step 7. Order Block (OB)

Order blocks represent **institutional accumulation zones**.

## Bullish Order Block

Last bearish candle before strong upward move.

### Detection

```
BullishOB =
    Candle[i] is bearish
AND
C[i+1] > H[i]
```

Zone:

```
OB_High = H[i]
OB_Low  = L[i]
```

---

## Bearish Order Block

Last bullish candle before strong downward move.

### Detection

```
BearishOB =
    Candle[i] is bullish
AND
C[i+1] < L[i]
```

Zone:

```
OB_High = H[i]
OB_Low  = L[i]
```

---

# Step 8. Fair Value Gap (FVG)

FVG is an **imbalance created by strong movement**.

## Bullish FVG

```
FVG =
    L[i+2] > H[i]
```

Gap zone:

```
FVG_low  = H[i]
FVG_high = L[i+2]
```

---

## Bearish FVG

```
FVG =
    H[i+2] < L[i]
```

Gap zone:

```
FVG_high = L[i]
FVG_low  = H[i+2]
```

---

# Step 9. Entry Model (Typical SMC Strategy)

## Buy Setup

1. Identify **bullish trend**
2. Wait for **sell-side liquidity sweep**
3. Identify **Bullish Order Block or Bullish FVG**
4. Wait for price to retrace to the zone

### Entry rule

```
Entry = OB or FVG zone
StopLoss = Below liquidity sweep
TakeProfit = Next swing high
```

---

## Sell Setup

1. Identify **bearish trend**
2. Wait for **buy-side liquidity sweep**
3. Identify **Bearish Order Block or Bearish FVG**
4. Wait for price retrace

### Entry rule

```
Entry = OB or FVG zone
StopLoss = Above liquidity sweep
TakeProfit = Next swing low
```

---

# Step 10. Risk Management

## Risk per trade

```
Risk = AccountBalance × RiskPercent
```

Example:

```
RiskPercent = 1%
```

---

## Position Size

```
PositionSize =
    Risk / (EntryPrice - StopLoss)
```

---

# Step 11. Full Algorithm Flow

```
1. Load OHLCV data
2. Detect swing highs and swing lows
3. Build market structure (HH HL LH LL)
4. Detect BOS
5. Detect CHoCH
6. Detect liquidity levels
7. Detect order blocks
8. Detect fair value gaps
9. Wait for liquidity sweep
10. Enter trade at OB/FVG
11. Set SL and TP
```

---

# Step 12. Simplified Pseudocode

```
for candle in candles:

    detectSwingHigh()
    detectSwingLow()

    updateMarketStructure()

    if BreakOfStructure():
        markTrend()

    detectLiquidity()

    detectOrderBlock()

    detectFVG()

    if liquiditySweep and priceAtOB:
        openTrade()
```
