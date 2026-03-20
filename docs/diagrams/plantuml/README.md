# PlantUML diagrams

This folder contains PlantUML diagrams for the microservices demo.

- `c4_system_context.puml` - C4 System Context diagram (uses C4-PlantUML include)
- `seq_placeorder.puml` - PlaceOrder (checkout) sequence
- `seq_cart.puml` - Cart flows (Add/Get/Empty)
- `seq_recommendations.puml` - Recommendation flow
- `seq_ads.puml` - Ad retrieval flow
- `seq_currency.puml` - Currency conversion flow
- `seq_payment.puml` - Payment charge flow
- `seq_shipping.puml` - Shipping quote and ship flow
- `seq_email.puml` - Email confirmation flow
- `seq_shoppingassistant.puml` - Shopping Assistant (RAG) flow

Render with a PlantUML tool or the VS Code PlantUML extension. Example:

```bash
# Render PNG from a .puml file
plantuml -tpng seq_placeorder.puml
```
