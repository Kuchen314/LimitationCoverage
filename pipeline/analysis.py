"""
Full analysis for the limitation-coverage study.

Reads the coverage table, runs every test reported in the Results section,
and prints results grouped by table.

Usage:
    python analysis.py coverage_table-FINAL.xlsx

Requires: pandas, numpy, scipy, openpyxl, scikit-learn
    pip install pandas numpy scipy openpyxl scikit-learn

Optional: pass a second CSV with columns  paper_id, review_words_r1,
review_words_r2, doc_chars_r1, doc_chars_r2  to enable the length checks.
"""

import sys
import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import rankdata
from sklearn.metrics import cohen_kappa_score


# ---------------------------------------------------------------- loading

def load(path):
    """Read the sheet and parse the 'n/d' coverage cells into numbers.

    The AVERAGE row holds a percentage like '52.3%' with no slash, so it is
    dropped first — otherwise the split below fails on it.
    """
    df = pd.read_excel(path)
    df = df[df["R1 Coverage"].astype(str).str.contains("/", na=False)].copy()

    for cond in ["R1", "R2"]:
        parts = df[f"{cond} Coverage"].astype(str).str.split("/")
        df[f"{cond}_cov"] = parts.str[0].astype(int)     # statements reproduced
        df[f"{cond}_lim"] = parts.str[1].astype(int)     # statements disclosed
        df[f"{cond}_frac"] = df[f"{cond}_cov"] / df[f"{cond}_lim"]

    # The same extracted list should be used for both conditions. If this
    # fails, the pairing is not exact and everything downstream is suspect.
    assert (df.R1_lim == df.R2_lim).all(), "denominators differ between conditions"

    return df.reset_index(drop=True)


# ---------------------------------------------------------------- helpers

def paired_battery(a, b, label, scale=1.0):
    """Run the full paired battery on two columns and return a dict.

    scale=100 expresses proportions as percentage points.

    Reports three tests making progressively weaker assumptions:
      t-test        assumes normal differences; gives the interpretable CI
      Wilcoxon      assumes only symmetric differences; ranks magnitudes
      sign test     assumes nothing; uses direction only
    Agreement across all three means the conclusion does not depend on
    distributional assumptions.
    """
    d = (a - b) * scale
    n = len(d)
    nonzero = d[d != 0]

    # rank-biserial: signed-rank statistic rescaled to [-1, 1]
    if len(nonzero) > 0:
        r = rankdata(nonzero.abs())
        rb = (r[nonzero > 0].sum() - r[nonzero < 0].sum()) / r.sum()
    else:
        rb = np.nan

    pos, neg = int((d > 0).sum()), int((d < 0).sum())

    out = {
        "label": label,
        "n": n,
        "mean_a": a.mean() * scale,
        "sd_a": a.std() * scale,
        "mean_b": b.mean() * scale,
        "sd_b": b.std() * scale,
        "mean_diff": d.mean(),
        "median_diff": d.median(),
        "sd_diff": d.std(),
        "pos": pos, "neg": neg, "tied": int((d == 0).sum()),
        "eff_n": len(nonzero),
        "d_z": d.mean() / d.std(ddof=1),      # paired d: SD *of differences*
        "rank_biserial": rb,
        "shapiro_p": stats.shapiro(d).pvalue if n <= 5000 else np.nan,
        "skew": stats.skew(d),
    }

    out["ci_lo"], out["ci_hi"] = stats.t.interval(
        0.95, n - 1, loc=d.mean(), scale=stats.sem(d)
    )

    t = stats.ttest_rel(a, b)
    out["t_stat"], out["t_p"] = t.statistic, t.pvalue
    out["wilcoxon_p"] = stats.wilcoxon(a, b).pvalue if len(nonzero) else np.nan
    out["sign_p"] = (stats.binomtest(pos, pos + neg, 0.5).pvalue
                     if pos + neg else np.nan)
    return out


def fmt_p(p):
    """One p-value convention everywhere, as the paper requires."""
    if pd.isna(p):
        return "n/a"
    return "<0.001" if p < 0.001 else f"{p:.3f}"


def rule(title):
    print(f"\n{'=' * 74}\n{title}\n{'=' * 74}")


# ---------------------------------------------------------------- analyses

def corpus(df):
    rule("TABLE 1 — CORPUS")
    lim = df.R1_lim
    print(f"  Papers                          {len(df)}")
    print(f"  Limitation statements, total    {lim.sum()}")
    print(f"  Per paper: median               {lim.median():.0f}")
    print(f"  Per paper: mean                 {lim.mean():.2f}")
    print(f"  Per paper: IQR                  {lim.quantile(.25):.0f}-{lim.quantile(.75):.0f}")
    print(f"  Per paper: range                {lim.min()}-{lim.max()}")


def coverage(df):
    rule("TABLE 2 — COVERAGE GAP")
    r = paired_battery(df.R1_frac, df.R2_frac, "coverage", scale=100)

    print(f"  Original                        {r['mean_a']:.1f}%  (SD {r['sd_a']:.1f})")
    print(f"  Redacted                        {r['mean_b']:.1f}%  (SD {r['sd_b']:.1f})")
    print(f"  Difference                      {r['mean_diff']:+.1f} pp (SD {r['sd_diff']:.1f})")
    print(f"  95% CI                          [{r['ci_lo']:.1f}, {r['ci_hi']:.1f}]")
    print()
    print(f"  Wilcoxon signed-rank            p = {fmt_p(r['wilcoxon_p'])}")
    print(f"  Paired t                        t = {r['t_stat']:.3f}, p = {fmt_p(r['t_p'])}")
    print(f"  Exact sign test                 p = {fmt_p(r['sign_p'])}")
    print()
    print(f"  Cohen's d_z                     {r['d_z']:.3f}")
    print(f"  Rank-biserial r                 {r['rank_biserial']:.3f}")
    print(f"  Shapiro-Wilk                    p = {fmt_p(r['shapiro_p'])}")
    print(f"  Skew                            {r['skew']:+.3f}")
    print()
    print(f"  Decreased / unchanged / increased   "
          f"{r['pos']} / {r['tied']} / {r['neg']}")
    print(f"  Effective n                     {r['eff_n']}")

    # counts are immune to varying denominators; report alongside proportions
    cg = df.R1_cov - df.R2_cov
    print(f"\n  Count difference (statements)   {cg.mean():+.3f} (SD {cg.std():.3f})")


def ratings(df):
    rule("TABLE 3 — RATING DIMENSIONS")
    dims = [("R1 Sound", "R2 Sound", "Soundness"),
            ("R1 Pres", "R2 Pres", "Presentation"),
            ("R1 Signif", "R2 Signif", "Significance"),
            ("R1 Orig", "R2 Orig", "Originality"),
            ("R1 Rec", "R2 Rec", "Recommendation")]

    print(f"  {'Dimension':<15}{'MeanD':>8}{'95% CI':>20}{'d_z':>8}"
          f"{'Wilc':>8}{'t':>8}{'Sign':>8}{'n':>6}{'Med':>5}")
    print("  " + "-" * 86)

    rows = []
    for a, b, name in dims:
        r = paired_battery(df[a], df[b], name)
        rows.append(r)
        ci = f"[{r['ci_lo']:+.3f}, {r['ci_hi']:+.3f}]"
        print(f"  {name:<15}{r['mean_diff']:>+8.3f}{ci:>20}{r['d_z']:>+8.3f}"
              f"{fmt_p(r['wilcoxon_p']):>8}{fmt_p(r['t_p']):>8}"
              f"{fmt_p(r['sign_p']):>8}{r['eff_n']:>6}{df[a].median():>5.0f}")

    # the bound quoted in the prose: widest interval edge across dimensions
    rubric = [max(abs(r["ci_lo"]), abs(r["ci_hi"])) for r in rows[:4]]
    rec = max(abs(rows[4]["ci_lo"]), abs(rows[4]["ci_hi"]))
    print(f"\n  Widest CI bound, rubric dims    {max(rubric):.3f}  "
          f"(quote as ~{np.ceil(max(rubric)*100)/100:.2f})")
    print(f"  Widest CI bound, recommendation {rec:.3f}  "
          f"(quote as ~{np.ceil(rec*100)/100:.2f})")


def decisions(df):
    rule("TABLE 4 — ACCEPT / REJECT")
    ct = pd.crosstab(df["R1 Decision"], df["R2 Decision"])
    print(ct.to_string().replace("\n", "\n  ").rjust(2))

    b = ct.loc["Accept", "Reject"]      # accept -> reject
    c = ct.loc["Reject", "Accept"]      # reject -> accept

    # McNemar's exact test is a binomial test on the discordant pairs only:
    # concordant pairs carry no information about a change.
    p = stats.binomtest(b, b + c, 0.5).pvalue
    k = cohen_kappa_score(df["R1 Decision"], df["R2 Decision"])

    acc1 = (df["R1 Decision"] == "Accept").sum()
    acc2 = (df["R2 Decision"] == "Accept").sum()
    print(f"\n  Accept rate, original           {acc1}/{len(df)} ({100*acc1/len(df):.1f}%)")
    print(f"  Accept rate, redacted           {acc2}/{len(df)} ({100*acc2/len(df):.1f}%)")
    print(f"  Discordant pairs                {b + c}  ({b} vs {c})")
    print(f"  McNemar (exact)                 p = {fmt_p(p)}")
    print(f"  Cohen's kappa                   {k:.3f}")


def checks(df):
    rule("TABLE 5 — CHECKS AND STRUCTURE")

    rho, p = stats.spearmanr(df.R1_frac, df.R2_frac)
    print(f"  Coverage, original vs redacted  rho = {rho:+.3f}, p = {fmt_p(p)}")

    # Overdispersion: if every statement had the same chance of being
    # reproduced, counts would be binomial and chi2/df would be ~1.
    pooled = df.R1_cov.sum() / df.R1_lim.sum()
    exp = df.R1_lim * pooled
    var = df.R1_lim * pooled * (1 - pooled)
    chi2 = (((df.R1_cov - exp) ** 2) / var).sum()
    dof = len(df) - 1
    print(f"  Overdispersion                  chi2 = {chi2:.1f}, df = {dof}, "
          f"ratio {chi2/dof:.2f}, p = {fmt_p(1 - stats.chi2.cdf(chi2, dof))}")

    rho, p = stats.spearmanr(df.R1_frac, df.R1_lim)
    print(f"  Coverage rate vs statement count  rho = {rho:+.3f}, p = {fmt_p(p)}")

    # Coarse denominators make ties mechanically more likely.
    tie = (df.R1_cov == df.R2_cov).astype(int)
    rho, p = stats.spearmanr(df.R1_lim, tie)
    print(f"  Tie probability vs count        rho = {rho:+.3f}, p = {fmt_p(p)}")

    print("\n  Tie rate by statement count:")
    for k, g in df.groupby("R1_lim"):
        if len(g) >= 5:
            t = (g.R1_cov == g.R2_cov).mean()
            print(f"    k={k:<3} n={len(g):<4} tied {100*t:.0f}%")


def length_checks(df, lengths):
    """Only runs if a lengths CSV is supplied."""
    rule("TABLE 5 (cont.) — LENGTH CHECKS")
    m = df.merge(lengths, left_on="Paper ID", right_on="paper_id", how="inner")
    print(f"  Matched {len(m)} of {len(df)} papers")
    if len(m) < len(df):
        print("  WARNING: unmatched papers dropped — check the join key")

    d_cov = m.R1_frac - m.R2_frac
    d_len = m.review_words_r1 - m.review_words_r2

    rho, p = stats.spearmanr(d_len, d_cov)
    print(f"  Length change vs coverage change  rho = {rho:+.3f}, p = {fmt_p(p)}")

    rho, p = stats.spearmanr(d_len, m["R1 Rec"] - m["R2 Rec"])
    print(f"  Length change vs score change     rho = {rho:+.3f}, p = {fmt_p(p)}")

    # Power law: coverage ~ length^slope. Slope 1 means proportional growth,
    # so the null here is 1, NOT 0 — linregress's own p-value tests 0.
    ok = (m.R1_cov > 0) & (m.review_words_r1 > 0)
    x, y = np.log(m.review_words_r1[ok]), np.log(m.R1_cov[ok])
    sl, ic, r, _, se = stats.linregress(x, y)
    z = (sl - 1) / se
    p = 2 * (1 - stats.norm.cdf(abs(z)))
    print(f"  Coverage vs review length (log-log)")
    print(f"    slope {sl:.3f} (SE {se:.3f}), z vs 1 = {z:+.2f}, p = {fmt_p(p)}")
    print(f"    n = {ok.sum()}, dropped {(~ok).sum()} zero-coverage papers")


def bootstrap(df, n_boot=10000, seed=0):
    """Clustered bootstrap: resample whole papers, not statements.

    Resampling individual statements would ignore that statements within a
    paper are not independent (the overdispersion check above shows they
    are not), and would give intervals that are too narrow.
    """
    rule("BOOTSTRAP (clustered on papers)")
    rng = np.random.default_rng(seed)
    idx = np.arange(len(df))
    diffs = np.empty(n_boot)
    for i in range(n_boot):
        s = df.iloc[rng.choice(idx, len(idx), replace=True)]
        diffs[i] = (s.R1_cov.sum() / s.R1_lim.sum()
                    - s.R2_cov.sum() / s.R2_lim.sum()) * 100
    lo, hi = np.percentile(diffs, [2.5, 97.5])
    print(f"  Pooled gap, {n_boot} resamples   {diffs.mean():+.2f} pp")
    print(f"  95% percentile CI               [{lo:.2f}, {hi:.2f}]")


# ---------------------------------------------------------------- main

def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "coverage_table-FINAL.xlsx"
    df = load(path)

    corpus(df)
    coverage(df)
    ratings(df)
    decisions(df)
    checks(df)
    bootstrap(df)

    if len(sys.argv) > 2:
        length_checks(df, pd.read_csv(sys.argv[2]))
    else:
        print("\n  [length checks skipped — pass a lengths CSV as the second "
              "argument to enable]")

    print("\nDone.\n")


if __name__ == "__main__":
    main()
