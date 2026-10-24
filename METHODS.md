# Method and interpretation notes

1. PriceUSD is the upstream field used; the project does not rename it an exchange
   closing price. `date` retains the source daily label. Consult the provider's
   metric methodology before mixing it with other feeds.
2. Deviation bps = (observed USD price / USD 1 - 1) × 10,000. The report measures
   both positive and negative deviations, with strictly greater-than exceedances.
3. Missing days remain missing. Exceedance fractions divide by observed days;
   missing calendar days are reported separately.
4. Recovery is confirmed on the third consecutive daily observation within the
   chosen band after the sample's lowest price. The count includes confirmation
   time; it is not the first recovery date, redemption timing or intraday duration.
5. The illustrative alert compares today's absolute deviation to the prior 30
   daily absolute deviations' mean plus three population standard deviations.
   All 30 prior dates must be present. A very quiet baseline can create many tiny
   alerts; no actionability, forecast skill or classification accuracy is claimed.
6. All thresholds and periods were chosen for descriptive teaching. Comparing
   USDC and DAI is not a causal control design; correlated prices can have shared
   exposures and cannot establish causal transmission.
7. A hypothetical position of 10,000 tokens has mark-to-peg shortfall
   max(0, (1 - minimum observed price) × 10,000) USD. This is neither actual loss
   nor a promise of redemption at par. Taxes, trading costs and slippage are absent.

## Regulatory reading to complete personally

HKMA's [stablecoin issuer regime page](https://www.hkma.gov.hk/eng/key-functions/international-financial-centre/stablecoin-issuers/)
states that the regime commenced on 1 August 2025. It motivates separate questions
about market price, reserves and redemption, none of which this price dataset can
fully answer. Do not apply present Hong Kong rules retrospectively to this 2023
sample or infer the local licensing status of either asset from its price.
The AI assistant located the source; the project owner has not yet confirmed
reading or independently explaining it. This is a learning checklist, not legal advice.
