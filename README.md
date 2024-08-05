
# Fivetran Streamlit Billing Model

## 📣 Overview
This Streamlit app showcases a variety of example reports, using simulated data from a fictional office supply company, to demonstrate the types of analyses possible within the Billing domain. These reports are built using different combinations of Fivetran connectors and data models, providing versatile examples of how to leverage Fivetran for billing analytics.

Supported connector and data model combinations include:

- [Stripe connector](https://fivetran.com/docs/connectors/applications/stripe) + [Stripe data model](https://fivetran.com/docs/transformations/data-models/stripe-data-model/stripe-transform-model)
- [Shopify connector](https://fivetran.com/docs/connectors/applications/shopify) + [Shopify data model](https://fivetran.com/docs/transformations/data-models/shopify-data-model/shopify-transform-model)
- [Recurly connector](https://fivetran.com/docs/connectors/applications/recurly) + [Recurly data model](https://fivetran.com/docs/transformations/data-models/recurly-data-model/recurly-transform-model)
- [Recharge connector](https://fivetran.com/docs/connectors/applications/recharge) + [Recharge data model](https://fivetran.com/docs/transformations/data-models/recharge-data-model/recharge-transform-model)
- [Zuora connector](https://fivetran.com/docs/connectors/applications/zuora) + [Zuora data model](https://fivetran.com/docs/transformations/data-models/zuora-data-model/zuora-transform-model)

Each data model provides a standardized, denormalized `*__line_item_enhanced` table that ensures consistent reporting across platforms. This means that regardless of your company's billing platform, these reports can be easily replicated using the platform-agnostic `*__line_item_enhanced` table.

## 📈 Example Reports
The app includes several example reports generated from the `*__line_item_enhanced` data model. These reports illustrate how you can analyze different aspects of billing data, with results segmented by product, location, and customer demographics.

| **Report** | **Description** |
|----------|-----------------|
| [Orders and Revenue](https://streamlit-fivetran-billing-model.streamlit.app/1_orders_and_revenue) | Showcases total revenue and orders over time and segmented by product, location, and customer. |
| [Subscription Report](https://streamlit-fivetran-billing-model.streamlit.app/2_subscriptions_report) | Highlights subscription activity and MRR and over time and segmented by subscription type. | 
| [Churn Analysis](https://streamlit-fivetran-billing-model.streamlit.app/3_churn_analysis) | Analyzes churn and retention rate as well as new MRR over time and provides a cohort analysis.  | 

## 🎯 Call to Action
These reports are designed to demonstrate the analytical capabilities when using Fivetran connectors paired with the corresponding transformation data models. We encourage you to explore these reports and provide feedback. If you find these examples useful or have suggestions for additional content, please share your thoughts via [GitHub issues](https://github.com/fivetran/streamlit_fivetran_billing_model/issues).