"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export function PassivoChart({
  dados,
}: {
  dados: { empresa: string; total: number }[];
}) {
  if (!dados.length) {
    return (
      <p className="py-10 text-center text-sm text-slate-400">
        Sem dados de passivo ainda.
      </p>
    );
  }

  const fmt = (v: number) =>
    v.toLocaleString("pt-BR", {
      notation: "compact",
      style: "currency",
      currency: "BRL",
    });

  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={dados} margin={{ top: 8, right: 8, left: 8, bottom: 8 }}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
        <XAxis
          dataKey="empresa"
          tick={{ fontSize: 12, fill: "#64748b" }}
          tickLine={false}
        />
        <YAxis
          tickFormatter={fmt}
          tick={{ fontSize: 11, fill: "#64748b" }}
          tickLine={false}
          axisLine={false}
          width={70}
        />
        <Tooltip
          formatter={(value) => [
            Number(value).toLocaleString("pt-BR", {
              style: "currency",
              currency: "BRL",
            }),
            "Passivo",
          ]}
          labelStyle={{ color: "#0f172a" }}
        />
        <Bar dataKey="total" fill="#0f172a" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
