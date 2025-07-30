library(ggplot2)
library(dplyr)
library(tidyr)
library(purrr)

# Load AD data
sock_AD_df <- read_csv('Descriptive statistics/sockshop/AD/sockshop_detailed_AD_results_with_levels.csv') %>%
  mutate(System = "sockshop")

train_AD_df <- read_csv('Descriptive statistics/trainticket/AD/trainticket_detailed_AD_results_with_levels.csv') %>%
  mutate(System = "trainticket")

ad_df <- bind_rows(sock_AD_df, train_AD_df)

# Load RCA data
sock_RCA_df <- read_csv('Descriptive statistics/sockshop/RCA/sockshop_detailed_RCA_results_with_levels.csv') %>%
  mutate(System = "sockshop")

train_RCA_df <- read_csv('Descriptive statistics/trainticket/RCA/trainticket_detailed_RCA_results_with_levels.csv') %>%
  mutate(System = "trainticket")

rca_df <- bind_rows(sock_RCA_df, train_RCA_df)


AD_PARAM_VALUES <- list(
  BIRCH    = c(low = "0.02", default = "0.045(d)", high = "0.065"),
  IFOREST  = c(low = "25", default = "100(d)", high = "200"),
  SVM      = c(low = "0.3", default = "0.5(d)", high = "0.7"),
  LOF      = c(low = "10", default = "20(d)", high = "35"),
  KNN      = c(low = "2", default = "5(d)", high = "10")
)

RCA_PARAM_VALUES <- list(
  MICRORCA = c(low = "0.3", default = "0.55(d)", high = "0.7"),
  RCD      = c(low = "4", default = "5(d)", high = "6"),
  CIRCA    = c(low = "0.01", default = "0.05(d)", high = "0.1")
)


plot_metric <- function(df, metrics, kind, output_dir, algo_col) {
  level_order <- c("low", "default", "high")
  system_order <- c("sockshop", "trainticket")
  system_display <- c(sockshop = "Sock Shop", trainticket = "Train Ticket")
  
  param_values <- if (kind == "Anomaly Detection") AD_PARAM_VALUES else RCA_PARAM_VALUES
  
  df[[algo_col]] <- toupper(df[[algo_col]])
  
  for (metric in metrics) {
    metric_df <- df %>% filter(Metric == metric)
    
    for (user_group in c(100, 1000)) {
      user_df <- metric_df %>% filter(Users == user_group)
      algorithms <- sort(unique(user_df[[algo_col]]))
      
      # Combine all algorithms' data
      plot_df <- map_dfr(algorithms, function(algo) {
        algo_df <- user_df %>% filter(!!sym(algo_col) == algo)
        
        map_dfr(system_order, function(sys) {
          map_dfr(level_order, function(lvl) {
            param_val <- param_values[[algo]][[lvl]]
            algo_df %>%
              filter(System == sys, Level == lvl) %>%
              mutate(
                System_Display = system_display[[sys]],
                Param = param_val,
                X = paste(System_Display, lvl, sep = "_"),
                Algo = algo
              )
          })
        })
      })
      
      # Set factor levels for ordering
      plot_df$Level <- factor(plot_df$Level, levels = level_order)
      plot_df$X <- factor(plot_df$X, levels = paste(rep(system_display, each = 3), level_order, sep = "_"))
      
      # Build x labels: only parameter values shown
      x_labels <- rep(unname(unlist(param_values[[plot_df$Algo[1]]][level_order])), times = 2)
      
      p <- ggplot(plot_df, aes(x = X, y = Value, fill = Level)) +
        geom_violin(scale = "width", trim = TRUE, color = "black", adjust = 2) +
        geom_boxplot(width = 0.2, position = position_dodge(0.9), outlier.shape = NA) +
        scale_x_discrete(labels = x_labels) +
        scale_fill_brewer(palette = "Set2") +
        labs(
          title = paste(kind, "-", metric, "-", user_group, "Users"),
          y = metric,
          x = NULL,
          fill = "Parameter Level"
        ) +
        facet_wrap(~ Algo, ncol = 3) + 
        theme_minimal(base_size = 14) +
        theme(
          strip.text = element_text(size = 16, face = "bold"),
          axis.text.x = element_text(size = 14, hjust = 0),
          axis.text.y = element_text(size = 14),
          axis.title.y = element_text(size = 16),
          plot.title = element_text(size = 18, hjust = 0.5),
          legend.title = element_text(size = 16),
          legend.text = element_text(size = 14),
          panel.grid.major.y = element_line(linetype = "dashed", color = "gray")
        ) +
        coord_cartesian(ylim = c(0, 1.05)) +
        annotate("text", x = 2, y = -0.05, label = "Sock Shop", 
                 vjust = 1.5, size = 5, fontface = "bold") +
        annotate("text", x = 5, y = -0.05, label = "Train Ticket", 
                 vjust = 1.5, size = 5, fontface = "bold")
      
      
      print(p)
      
      # Optional: save
      # ggsave(filename = paste0(output_dir, "/", kind, "_", metric, "_", user_group, "_ALL_ALGOS.png"),
      #        plot = p, width = 4 * length(algorithms), height = 5)
    }
  }
}



# Plot AD metrics
ad_metrics <- c("Precision", "Recall", "F-Score")
plot_metric(ad_df, ad_metrics, kind = "Anomaly Detection", output_dir = "descriptive_plots/AD", algo_col = "Algorithm")

# Plot RCA metrics
rca_metrics <- c("Precision@1", "Precision@2", "Precision@3")
plot_metric(rca_df, rca_metrics, kind = "Root Cause Analysis", output_dir = "descriptive_plots/RCA", algo_col = "Model")
