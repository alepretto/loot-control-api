# Loot Control — Design System (Tema V2)

> Este documento consolida **todo** o sistema visual do frontend atual.
> É a única coisa que estamos mantendo do V1 — referência única para o rebuild.

---

## 1. Paleta de Cores

### Frontend (Tailwind — `tailwind.config.ts`)

| Token               | Hex         | Uso                                    |
|---------------------|-------------|----------------------------------------|
| `background`        | `#070B11`   | Fundo principal do app                 |
| `surface`           | `#0E1218`   | Cards, sidebar, modais                 |
| `surface-2`         | `#141A22`   | Headers de tabela, hover states        |
| `surface-3`         | `#1C2330`   | Botões, inputs, estados ativos         |
| `border`            | `#20282F`   | Bordas de cards, divisores             |
| `primary`           | `#2563eb`   | Ações principais, links, selecionado  |
| `primary-hover`     | `#1d4ed8`   | Hover em botões primary                |
| `accent`            | `#22c55e`   | Sucesso, receitas, positivo            |
| `danger`            | `#ef4444`   | Erro, exclusão, custos variáveis       |
| `muted`             | `#8b949e`   | Texto secundário, labels, placeholders  |
| `text-primary`      | `#e6edf3`   | Texto principal                         |
| `text-secondary`    | `#7d8590`   | Texto terciário                         |

### Mockup (HTML — `:root` CSS vars)

Estes são os valores **originais** do mockup interativo. A versão Tailwind acima
é uma adaptação ligeiramente diferente. Manter a do mockup como referência original:

| Token              | Valor                        | Nota                          |
|--------------------|------------------------------|-------------------------------|
| `--bg`             | `#07090C`                   | Um tom mais escuro que o Tailwind |
| `--bg-2`           | `#0E1217`                   | Equivalente ao `surface`      |
| `--bg-2-hi`        | `#11161C`                   | Hover sutil                   |
| `--bg-3`           | `#171C24`                   | Equivalente ao `surface-2/3`  |
| `--border`         | `#1F2730`                   |                               |
| `--border-hi`      | `#2A3440`                   | Hover em bordas               |
| `--fg`             | `#E8ECF1`                   | Texto principal               |
| `--dim`            | `#98A2B3`                   | Texto secundário               |
| `--dim-2`          | `#667085`                   | Texto terciário                |
| `--primary`        | `oklch(0.78 0.12 210)`     | Cyan (hue 210)                |
| `--primary-dim`    | `oklch(0.5 0.1 210)`       | Primary com baixa luminância   |
| `--up`             | `oklch(0.76 0.15 150)`     | Verde — receitas/ganhos       |
| `--dn`             | `oklch(0.70 0.18 25)`      | Vermelho — custos/perdas       |
| `--warn`           | `oklch(0.80 0.14 70)`      | Âmbar — avisos                 |

**Decisão:** O frontend em produção usa os hex do Tailwind. O mockup usa oklch.
Para consistência no rebuild, **usar os valores do Tailwind** como verdadieros,
mas manter os oklch do mockup para casos que precisam de manipulação dinâmica de cor
(badges por natureza, etc.).

---

## 2. Natureza (Cores por tipo de transação)

Cada natureza de transação tem cor dedicada, usada em badges, gráficos e indicadores:

| Natureza            | Label           | Cor hex    | oklch (mockup)             | Hue  |
|---------------------|-----------------|------------|------------------------------|------|
| `income`            | Receita         | `#22c55e` | `oklch(0.76 0.15 150)`     | 150  |
| `fixed_expense`     | Custo Fixo      | `#f97316` | `oklch(0.78 0.14 25)`      | 25   |
| `variable_expense`  | Custo Variável  | `#ef4444` | `oklch(0.70 0.18 10)`      | 10   |
| `investment`        | Investimento    | `#2563eb` | `oklch(0.78 0.12 210)`     | 210  |

**Short labels:** REC, FIX, VAR, INV

---

## 3. Tipografia

| Papel          | Família                                       | Peso     | Uso                        |
|----------------|-----------------------------------------------|----------|----------------------------|
| Sans-serif     | `Outfit` (Google Fonts) → `var(--font-sans)`  | 400–600  | Texto geral, títulos       |
| Monospace      | `JetBrains Mono` → `var(--font-mono)`        | 400–600  | Valores, dados, badges     |

**Fallback stack sans:** `ui-sans-serif, system-ui, sans-serif`
**Fallback stack mono:** `ui-monospace, monospace`

### Tamanhos base (do mockup)

| Contexto       | Tamanho | Line-height |
|----------------|---------|-------------|
| Base (mobile)  | 13px    | 1.4         |
| Desktop        | 15px    | 1.4         |

### Classes de tipografia (Tailwind)

```
text-text-primary    → texto principal (#e6edf3)
text-text-secondary  → texto secundário (#7d8590)
text-muted           → texto terciário/labels (#8b949e)
font-mono tabular-nums → alinhamento numérico (valores financeiros)
```

### Font data (para dados financeiros)

```css
.font-data {
  font-family: var(--font-mono), monospace;
  font-feature-settings: "tnum";
  font-variant-numeric: tabular-nums;
}
```

---

## 4. Layout Padrão

### Espaçamento

| Contexto              | Valor            |
|-----------------------|------------------|
| Wrapper de página     | `px-4 md:px-6 py-5 space-y-5` |
| Cards                 | `bg-surface border border-border rounded-xl` |
| Padding de card       | `p-4` a `p-6`   |
| Gap entre seções      | `gap-4` (16px)   |
| Gap em grid/cards     | `gap-3` (12px)   |

### Grid de transações (desktop)

```
TX_GRID = "grid-cols-[100px_85px_minmax(180px,1.2fr)_minmax(120px,1fr)_minmax(140px,1fr)_110px_44px]"
```
Colunas: Data | Natureza | Descrição | Taxonomia | Conta/Método | Valor | Ações

### Sidebar

- Largura: `w-56` (224px)
- Item ativo: `bg-primary/10 text-primary` com indicador lateral 2px `#2563eb` com box-shadow glow
- Item inativo: `text-muted hover:bg-surface-2 hover:text-text-primary`

---

## 5. Componentes Visuais

### Cards

```
bg-surface border border-border rounded-xl p-4 md:p-6
```

Hover (quando interativo):
```
hover:bg-surface-2/60 transition-colors
```

### Badges (Pill / Nature)

```css
/* Badges de natureza — fundo 15% opacidade, borda 30% opacidade */
background-color: ${color}15;
border: 1px solid ${color}30;
color: ${color};
```

Textos curtos: `text-[9px] font-semibold px-1.5 py-0.5 rounded`

### Botões

| Tipo           | Classes                                        |
|----------------|------------------------------------------------|
| Ghost          | `text-muted hover:text-text-primary hover:bg-surface-2 transition-colors` |
| Primary        | `bg-primary hover:bg-primary-hover text-white rounded-lg` |
| Danger         | `text-danger hover:bg-danger/10`               |
| Confirm delete | `bg-danger/15 text-danger border border-danger/30` |

### Modais

```
fixed inset-0 z-50 flex items-center justify-center p-4
backdrop: bg-black/60 backdrop-blur-sm
content: bg-surface-2 border border-border rounded-2xl w-full max-w-sm p-6 shadow-2xl
```

### Tabelas (Sheet Table)

```css
.sheet-table { @apply w-full border-collapse; }
.sheet-table th {
  @apply bg-surface-2 text-muted text-xs font-medium uppercase tracking-wider
         px-3 py-2 text-left border-b border-r border-border sticky top-0 z-10;
  font-family: var(--font-mono), monospace;
  letter-spacing: 0.04em;
}
.sheet-table td {
  @apply px-3 py-1.5 text-sm text-text-primary border-b border-r border-border;
}
.sheet-table tr:hover td { @apply bg-surface-2; }
```

### Scrollbar

```css
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #20282F; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #2d3748; }
```

### Selection

```css
::selection {
  background-color: rgba(37, 99, 235, 0.28);
  color: #e6edf3;
}
```

---

## 6. Efeitos Visuais

### Glow / Sombras

| Token             | Valor                                                                         |
|-------------------|-------------------------------------------------------------------------------|
| `glow-primary`    | `0 0 28px rgba(37, 99, 235, 0.22), 0 0 8px rgba(37, 99, 235, 0.1)`          |
| `glow-accent`     | `0 0 28px rgba(34, 197, 94, 0.18)`                                           |
| `glow-danger`     | `0 0 28px rgba(239, 68, 68, 0.18)`                                           |
| `glow-sm`         | `0 0 12px rgba(37, 99, 235, 0.12)`                                           |

Sidebar active indicator glow: `0 0 8px rgba(37, 99, 235, 0.6)`

### Dot-grid texture (fundo do body)

```css
body {
  background-image: radial-gradient(
    circle at 1px 1px,
    rgba(32, 40, 47, 0.55) 1px,
    transparent 0
  );
  background-size: 28px 28px;
}
```

---

## 7. Animações

### Fade Up

```css
@keyframes fade-up {
  from { opacity: 0; transform: translateY(14px); }
  to   { opacity: 1; transform: translateY(0); }
}

.animate-fade-up {
  animation: fade-up 0.5s ease-out forwards;
}
```

### Fade In

```css
@keyframes fade-in {
  from { opacity: 0; }
  to   { opacity: 1; }
}

.animate-fade-in {
  animation: fade-in 0.4s ease-out forwards;
}
```

### Stagger (filhos com delay sequencial)

```css
.animate-stagger > * {
  animation: fade-up 0.5s ease-out both;
}
.animate-stagger > *:nth-child(1) { animation-delay: 0ms; }
.animate-stagger > *:nth-child(2) { animation-delay: 70ms; }
.animate-stagger > *:nth-child(3) { animation-delay: 140ms; }
.animate-stagger > *:nth-child(4) { animation-delay: 210ms; }
.animate-stagger > *:nth-child(5) { animation-delay: 280ms; }
.animate-stagger > *:nth-child(6) { animation-delay: 350ms; }
```

---

## 8. Ícones

Estilo: outline, `strokeWidth={1.75}` ou `{2}`, sem preenchimento.
Tamanho padrão: `w-4 h-4` (16px), detalhes: `w-3.5 h-3.5` (14px).

Origem: SVG inline (Lucide-style), **não** biblioteca de ícones instalada.

---

## 9. Navegação (Sidebar)

### Items principais (MAIN_NAV)

| Rota            | Label           | Ícone (descrição)          |
|-----------------|-----------------|----------------------------|
| `/painel`       | Painel          | Home/layout dashboard      |
| `/lancamentos`  | Lançamentos     | Lista/receipt               |
| `/patrimonio`   | Patrimônio      | Bar chart                   |
| `/investimentos`| Investimentos   | Trending up                 |
| `/contas`       | Contas          | Credit card/wallet          |
| `/resumo`       | Resumo          | Tree/list hierarchy          |

### Items de gestão (MANAGE_NAV)

| Rota            | Label           | Ícone                        |
|-----------------|-----------------|------------------------------|
| `/recorrencias` | Recorrências    | Clock/repeat                 |
| `/tags`         | Tags            | Tag                          |
| `/orcamentos`   | Orçamentos      | Target/pie                   |
| `/passivos`     | Passivos        | Trending down                |

### Ticker (rodapé da sidebar)

Mostra cotações: USD, BTC, IBOV — atualizadas via SettingsContext.

---

## 10. Configuração Tailwind Completa

```typescript
// tailwind.config.ts
import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        background: "#070B11",
        surface: "#0E1218",
        "surface-2": "#141A22",
        "surface-3": "#1C2330",
        border: "#20282F",
        primary: "#2563eb",
        "primary-hover": "#1d4ed8",
        accent: "#22c55e",
        danger: "#ef4444",
        muted: "#8b949e",
        "text-primary": "#e6edf3",
        "text-secondary": "#7d8590",
      },
      fontFamily: {
        sans: ["var(--font-sans)", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "monospace"],
      },
      boxShadow: {
        "glow-primary": "0 0 28px rgba(37, 99, 235, 0.22), 0 0 8px rgba(37, 99, 235, 0.1)",
        "glow-accent": "0 0 28px rgba(34, 197, 94, 0.18)",
        "glow-danger": "0 0 28px rgba(239, 68, 68, 0.18)",
        "glow-sm": "0 0 12px rgba(37, 99, 235, 0.12)",
      },
      animation: {
        "fade-up": "fade-up 0.5s ease-out forwards",
        "fade-in": "fade-in 0.4s ease-out forwards",
      },
      keyframes: {
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(14px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "fade-in": {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
```

---

## 11. CSS Global Completo

```css
/* globals.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  background-color: #070B11;
  color: #e6edf3;
  font-size: 15px;
  background-image: radial-gradient(circle at 1px 1px, rgba(32, 40, 47, 0.55) 1px, transparent 0);
  background-size: 28px 28px;
}

@media (min-width: 768px) {
  html { font-size: 15px; }
}

.sheet-table { @apply w-full border-collapse; }
.sheet-table th {
  @apply bg-surface-2 text-muted text-xs font-medium uppercase tracking-wider
         px-3 py-2 text-left border-b border-r border-border sticky top-0 z-10;
  font-family: var(--font-mono), monospace;
  letter-spacing: 0.04em;
}
.sheet-table td { @apply px-3 py-1.5 text-sm text-text-primary border-b border-r border-border; }
.sheet-table tr:hover td { @apply bg-surface-2; }

.font-data {
  font-family: var(--font-mono), monospace;
  font-feature-settings: "tnum";
  font-variant-numeric: tabular-nums;
}

::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #20282F; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #2d3748; }

::selection { background-color: rgba(37, 99, 235, 0.28); color: #e6edf3; }

@keyframes fade-up {
  from { opacity: 0; transform: translateY(14px); }
  to   { opacity: 1; transform: translateY(0); }
}
@keyframes fade-in {
  from { opacity: 0; }
  to   { opacity: 1; }
}

.animate-stagger > * { animation: fade-up 0.5s ease-out both; }
.animate-stagger > *:nth-child(1) { animation-delay: 0ms; }
.animate-stagger > *:nth-child(2) { animation-delay: 70ms; }
.animate-stagger > *:nth-child(3) { animation-delay: 140ms; }
.animate-stagger > *:nth-child(4) { animation-delay: 210ms; }
.animate-stagger > *:nth-child(5) { animation-delay: 280ms; }
.animate-stagger > *:nth-child(6) { animation-delay: 350ms; }

.nav-active-indicator { position: relative; }
.nav-active-indicator::before {
  content: '';
  position: absolute;
  left: 0; top: 20%; bottom: 20%;
  width: 2px;
  border-radius: 0 2px 2px 0;
  background: #2563eb;
  box-shadow: 0 0 8px rgba(37, 99, 235, 0.6);
}

.glow-primary { box-shadow: 0 0 28px rgba(37, 99, 235, 0.2), 0 0 8px rgba(37, 99, 235, 0.08); }
.glow-accent  { box-shadow: 0 0 28px rgba(34, 197, 94, 0.18); }
```

---

## 12. Fontes (Next.js setup)

```typescript
// layout.tsx — carregamento de fontes
import { Outfit, JetBrains_Mono } from "next/font/google";

const outfit = Outfit({ subsets: ["latin"], variable: "--font-sans", display: "swap" });
const jetbrainsMono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-mono", display: "swap" });

// <html lang="pt-BR" className="dark">
// <body className={`${outfit.variable} ${jetbrainsMono.variable} bg-background text-text-primary antialiased font-sans`}>
```

**themeColor:** `#0E1218` (surface)

---

## 13. Responsividade

- Mobile-first design com breakpoints `md:` (768px)
- Sidebar colapsa em mobile, visível em desktop
- Tabelas usam versão card em mobile, grid em desktop (`hidden md:grid`)
- Transações mobile: card vertical com dot de cor por natureza

---

## 14.decisões de design registradas no CLAUDE.md

- **Paleta:** `#070B11` bg, `#2563eb` primary, `#22c55e` accent, `#ef4444` danger
- **Nature labels completos** — "Receita", "Custo Fixo", "Custo Variável", "Investimento" (não abreviações)
- **Modal centralizado** para edição de transações (não bottom sheet)
- **Busca client-side** em Lançamentos
- **Padrão de layout:** wrapper `px-4 md:px-6 py-5 space-y-5`, cards `bg-surface border border-border rounded-xl`