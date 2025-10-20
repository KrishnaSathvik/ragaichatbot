# Streaming Data Pipeline SLA - Walgreens Real-time Analytics

## SLA Requirements
- **Data freshness**: 10 minutes maximum lag
- **Availability**: 99.5% uptime
- **Throughput**: 50,000 events per minute
- **Data quality**: 99.9% accuracy (no duplicates, no missing data)

## Architecture Components
- **Structured Streaming**: Spark streaming with 1-minute micro-batches
- **Watermark**: 10 minutes for late data handling
- **Checkpointing**: Every 30 seconds for fault tolerance
- **Backpressure**: Automatic throttling when downstream is slow

## Performance Metrics
- **Current lag**: 3.2 minutes average (well within 10-minute SLA)
- **Uptime**: 99.7% (exceeds 99.5% requirement)
- **Throughput**: 65,000 events/minute (30% above requirement)
- **Data quality**: 99.95% accuracy (exceeds 99.9% requirement)

## Late Data Handling
- **Watermark strategy**: 10-minute watermark with 2-minute grace period
- **Late data policy**: Merge with existing records, update timestamps
- **Dropped events**: <0.1% (only extremely late data)
- **Recovery process**: Replay from checkpoint on failure

## Monitoring and Alerting
- **Lag monitoring**: Alert when lag > 8 minutes
- **Throughput monitoring**: Alert when < 40,000 events/minute
- **Error rate**: Alert when > 0.5% error rate
- **Checkpoint health**: Alert when checkpoint fails

## Incident Response
- **P0 incidents**: 1 in 6 months (resolved in 8 minutes)
- **P1 incidents**: 3 in 6 months (average resolution: 25 minutes)
- **Recovery time**: <5 minutes for most failures
- **Data loss**: 0 events lost in 6 months

## Cost Optimization
- **Auto-scaling**: Scale up during peak hours, down during off-peak
- **Resource allocation**: Right-sized clusters based on actual usage
- **Storage optimization**: Compress old data, archive after 90 days
- **Total cost**: $8,500/month (30% reduction from initial setup)

## Key Learnings
The watermark strategy was crucial for handling late data without losing events. The 10-minute watermark with 2-minute grace period works well for our use case. Auto-scaling saved us significant costs during off-peak hours. The checkpointing every 30 seconds was the right balance between performance and fault tolerance.
