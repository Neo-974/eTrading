import React, { useState, useEffect } from 'react';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
import { Typography, Box, CircularProgress } from '@mui/material';
import { TradingAPI } from '../api/client';

function fmt(ts) {
  return new Date(ts).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
}

export default function Charts({ symbol = 'EURUSD' }) {
  const [candles, setCandles] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    try {
      const [c, ind] = await Promise.all([TradingAPI.candles(symbol, 50), TradingAPI.indicators(symbol)]);
      const bb = ind?.bollinger;
      const data = c.map((candle) => ({
        name: fmt(candle.time),
        price: parseFloat(candle.close.toFixed(5)),
        upper: bb ? parseFloat(bb.upper.toFixed(5)) : undefined,
        lower: bb ? parseFloat(bb.lower.toFixed(5)) : undefined,
      }));
      setCandles(data);
    } catch (e) {
      console.error('Charts fetch error:', e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    const id = setInterval(load, 10000);
    return () => clearInterval(id);
  }, [symbol]);

  if (loading) return <Box sx={{ display: 'flex', justifyContent: 'center', pt: 4 }}><CircularProgress /></Box>;

  return (
    <Box>
      <Typography variant="subtitle1" fontWeight={700} mb={1}>{symbol} M15 - Prix + Bollinger</Typography>
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={candles} margin={{ top: 5, right: 10, bottom: 5, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#333" />
          <XAxis dataKey="name" tick={{ fontSize: 10 }} interval="preserveStartEnd" />
          <YAxis domain={['auto', 'auto']} tick={{ fontSize: 10 }} width={70} />
          <Tooltip contentStyle={{ background: '#1e1e1e', border: '1px solid #444' }} formatter={(val) => val?.toFixed(5)} />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Line type="monotone" dataKey="price" stroke="#90caf9" dot={false} name="Prix" strokeWidth={2} />
          <Line type="monotone" dataKey="upper" stroke="#ff9800" dot={false} name="BB Haute" strokeDasharray="4 4" strokeWidth={1} />
          <Line type="monotone" dataKey="lower" stroke="#4caf50" dot={false} name="BB Basse" strokeDasharray="4 4" strokeWidth={1} />
        </LineChart>
      </ResponsiveContainer>
    </Box>
  );
}
