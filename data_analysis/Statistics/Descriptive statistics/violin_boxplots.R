library(tidyverse)
library(ggplot2)

# Add Dataset labels
ts_normal_data$Behavior <- "Normal"
ts_anomalous_data$Behavior <- "Anomalous"

# Combine datasets
# combined_data <- rbind(normal_data, anomalous_data)
combined_data <- ts_anomalous_data

# Define the threshold for "close to 0" and the proportion limit
zero_threshold <- 1  # Threshold for values considered close to 0
proportion_limit <- 0.85  # Remove columns where >95% of values are close to 0

# Identify numeric columns only
numeric_columns <- sapply(combined_data, is.numeric)

# Identify columns to keep based on the threshold
columns_to_keep <- sapply(combined_data[, numeric_columns], function(col) {
  mean(abs(col) > zero_threshold) > (1 - proportion_limit)  # Check if the proportion of "non-zero" values is above the limit
})

columns_to_keep <- columns_to_keep[!is.na(columns_to_keep)]

# Print the names of removed columns (optional)
# removed_columns <- names(columns_to_keep[!columns_to_keep])
# print("Removed columns:")
# print(removed_columns)

# Ensure that the factors are not removed
columns_to_retain <- c("Behavior", "scenario", "service", "users")
filtered_data <- combined_data[, c(columns_to_retain, names(columns_to_keep[columns_to_keep]))]

# Filter columns that end with _energy, _cpu, _memory_rss
metrics_columns <- colnames(filtered_data)[grepl("_energy$|_cpu$|_memory_rss$", colnames(filtered_data))]
filtered_data <- filtered_data[, c(columns_to_retain, metrics_columns)]

# Define metric types
cpu_columns <- colnames(filtered_data)[grepl("_cpu$", colnames(filtered_data))]
memory_columns <- colnames(filtered_data)[grepl("_memory_rss$", colnames(filtered_data))]
energy_columns <- colnames(filtered_data)[grepl("_energy$", colnames(filtered_data))]

metric_types <- list(
  "CPU" = cpu_columns,
  "Memory (RSS)" = memory_columns,
  "Energy" = energy_columns
)

# Generate plots for the "Energy" metric type
metric_type <- "Energy"
columns <- metric_types[[metric_type]]
library(tidyr)
metric_data <- pivot_longer(
  filtered_data,
  cols = all_of(columns),
  names_to = "Metric",
  values_to = "Value"
)

# Define the custom order for the x-axis labels
# custom_order <- c("ts-seat-service_energy", "ts-auth-service_energy", "ts-basic-service_energy",
# "ts-order-service_energy", "ts-route-service_energy", "ts-station-service_energy", "ts-ticketinfo-service_energy", "ts-train-service_energy", "ts-travel-service_energy", "ts-travel2-service_energy", "ts-user-service_energy", "ts-admin-user-service_energy")

# Reorder the Metric variable based on the custom order
# metric_data$Metric <- factor(metric_data$Metric, levels = custom_order)
metric_data$Behavior <- factor(metric_data$Behavior, levels = c("Normal", "Anomalous"))

# metric_data$service <- factor(metric_data$service, levels = c("front-end", "orders"))
metric_data$service <- factor(metric_data$service, levels = c("ts-travel-service", "ts-order-service"))
# metric_data$scenario <- factor(metric_data$scenario, levels = c("scenario_A", "scenario_B"), labels = c("Browse Catalogue", "Create Order"))
metric_data$scenario <- factor(metric_data$scenario, levels = c("scenario_A", "scenario_B"), labels = c("Search Tickets", "Book Ticket"))
metric_data$users <- factor(metric_data$users, levels = c(100, 1000), labels = c("100 Users", "1000 Users"))

# Anomalous vs Normal
# ggplot(metric_data, aes(x = Metric, y = Value, fill = Behavior)) +
#   geom_violin(trim = TRUE, scale = "width", color = "black", adjust = 2) +
#   geom_boxplot(width = 0.2, position = position_dodge(0.9), outlier.shape = NA) +
#   labs(
#     title = paste("Comparison of", metric_type, "Metrics Between Normal and Anomalous Behaviors"),
#     x = paste(metric_type, "Metrics"),
#     y = "Energy Consumption (J)",
#     fill = "Behavior"
#   ) +
#   theme_minimal() +
#   theme(
#     plot.title = element_text(size = 22, hjust = 0.5),  # Larger title
#     axis.title.x = element_text(size = 22),  # Larger x-axis label
#     axis.title.y = element_text(size = 22),  # Larger y-axis label
#     axis.text.x = element_text(size = 22, angle = -30, hjust = 0),
#     # axis.text.x = element_text(size = 14.5, angle = 45, hjust = 1),  # Larger x-axis tick labels
#     axis.text.y = element_text(size = 22),  # Larger y-axis tick labels
#     legend.title = element_text(size = 22),  # Larger legend title
#     legend.text = element_text(size = 22)   # Larger legend text
#   ) +
#   scale_fill_manual(values = c("Normal" = "#ADD8E6", "Anomalous" = "#FFB6C1")) +
#   theme(panel.grid.major.y = element_line(linetype = "dashed", color = "gray")) +
#   ylim(0, 40)
# 
# ggsave("violin_plot_energy.png", width = 16, height = 9, dpi = 300)

# Service Plot
ggplot(metric_data, aes(x = Metric, y = Value, fill = service)) +
  # geom_violin(trim = TRUE, scale = "width", color = "black", adjust = 2) +
  geom_boxplot(width = 0.2, position = position_dodge(0.9), outlier.shape = NA) +
  labs(
    title = paste("Comparison of", metric_type, "Metrics by Stressed Service"),
    x = paste(metric_type, "Metrics"),
    y = "Energy Consumption (J)",
    fill = "Service Stressed"
  ) +
  theme_minimal() +
  theme(
    plot.title = element_text(size = 22, hjust = 0.5),  # Larger title
    axis.title.x = element_text(size = 22),  # Larger x-axis label
    axis.title.y = element_text(size = 22),  # Larger y-axis label
    # axis.text.x = element_text(size = 22, angle = 45, hjust = 1),
    axis.text.x = element_text(size = 22, angle = -30, hjust = 0),  # Larger x-axis tick labels
    axis.text.y = element_text(size = 22),  # Larger y-axis tick labels
    legend.title = element_text(size = 22),  # Larger legend title
    legend.text = element_text(size = 22)   # Larger legend text
  ) +
  scale_fill_manual(values = c("ts-travel-service" = "#ADD8E6", "ts-order-service" = "#FFB6C1")) +
  # scale_fill_manual(values = c("front-end" = "#ADD8E6", "orders" = "#FFB6C1")) +
  theme(panel.grid.major.y = element_line(linetype = "dashed", color = "gray")) +
  ylim(0, 40)

ggsave("ts-box_plot_service.png", width = 16, height = 9, dpi = 300)

# Scenario Plot
ggplot(metric_data, aes(x = Metric, y = Value, fill = scenario)) +
  # geom_violin(trim = TRUE, scale = "width", color = "black", adjust = 2) +
  geom_boxplot(width = 0.2, position = position_dodge(0.9), outlier.shape = NA) +
  labs(
    title = paste("Comparison of", metric_type, "Metrics by Scenario"),
    x = paste(metric_type, "Metrics"),
    y = "Energy Consumption (J)",
    fill = "Scenario"
  ) +
  theme_minimal() +
  theme(
    plot.title = element_text(size = 22, hjust = 0.5),  # Larger title
    axis.title.x = element_text(size = 22),  # Larger x-axis label
    axis.title.y = element_text(size = 22),  # Larger y-axis label
    # axis.text.x = element_text(size = 18, angle = 45, hjust = 1),
    axis.text.x = element_text(size = 22, angle = -30, hjust = 0),  # Larger x-axis tick labels
    axis.text.y = element_text(size = 22),  # Larger y-axis tick labels
    legend.title = element_text(size = 22),  # Larger legend title
    legend.text = element_text(size = 22)   # Larger legend text
  ) +
  scale_fill_manual(values = c("Search Tickets" = "#ADD8E6", "Book Ticket" = "#FFB6C1")) +
  # scale_fill_manual(values = c("Browse Catalogue" = "#ADD8E6", "Create Order" = "#FFB6C1")) +
  theme(panel.grid.major.y = element_line(linetype = "dashed", color = "gray")) +
  ylim(0, 40)
ggsave("ts-box_plot_scenario.png", width = 16, height = 9, dpi = 300)

# Users Plot
ggplot(metric_data, aes(x = Metric, y = Value, fill = users)) +
  # geom_violin(trim = TRUE, scale = "width", color = "black", adjust = 2) +
  geom_boxplot(width = 0.2, position = position_dodge(0.9), outlier.shape = NA) +
  labs(
    title = paste("Comparison of", metric_type, "Metrics by User Load"),
    x = paste(metric_type, "Metrics"),
    y = "Energy Consumption (J)",
    fill = "Concurrent Users"
  ) +
  theme_minimal() +
  theme(
    plot.title = element_text(size = 22, hjust = 0.5),  # Larger title
    axis.title.x = element_text(size = 22),  # Larger x-axis label
    axis.title.y = element_text(size = 22),  # Larger y-axis label
    # axis.text.x = element_text(size = 18, angle = 45, hjust = 1),
    axis.text.x = element_text(size = 22, angle = -30, hjust = 0),  # Larger x-axis tick labels
    axis.text.y = element_text(size = 22),  # Larger y-axis tick labels
    legend.title = element_text(size = 22),  # Larger legend title
    legend.text = element_text(size = 22)   # Larger legend text
  ) +
  scale_fill_manual(values = c("100 Users" = "#ADD8E6", "1000 Users" = "#FFB6C1")) +
  theme(panel.grid.major.y = element_line(linetype = "dashed", color = "gray")) +
  ylim(0, 40)
ggsave("ts-box_plot_users.png", width = 16, height = 9, dpi = 300)
