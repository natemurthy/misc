// NOTE task scheduling snippets

use once_cell::sync::Lazy;
use std::sync::{Arc, Mutex};
use tokio::task::JoinHandle;
use tracing::{error, info};

type SchedulingError = String;

// Global state to track the current running schedule
static CURRENT_SCHEDULE: Lazy<Arc<Mutex<Option<JoinHandle<()>>>>> =
    Lazy::new(|| Arc::new(Mutex::new(None)));

// Task function stand-in for dummy control action
fn set_real_power_w(p: i32) {
    info!("Setting power to {} W", p);
}

// Parse time string in "%H:%M:%S" format and convert to SystemTime for today
fn parse_time_today(time_str: &str) -> Result<std::time::SystemTime, SchedulingError> {
    use chrono::{Local, NaiveTime, TimeZone};

    let time = NaiveTime::parse_from_str(time_str, "%H:%M:%S")
        .map_err(|e| format!("Invalid time format '{}': {}", time_str, e))?;

    let now = Local::now();
    let today = now.date_naive().and_time(time);

    // Convert to SystemTime
    let datetime = Local
        .from_local_datetime(&today)
        .single()
        .ok_or_else(|| "Ambiguous or invalid time".to_string())?;

    Ok(datetime.into())
}

// Parse simple ISO 8601 duration (e.g., "3S", "5M", "1H")
fn parse_iso8601_duration(duration_str: &str) -> Result<std::time::Duration, SchedulingError> {
    let duration_str = duration_str.trim();
    if duration_str.is_empty() {
        return Err("Empty duration string".to_string());
    }

    let (value_str, unit) = duration_str.split_at(duration_str.len() - 1);
    let value: u64 = value_str
        .parse()
        .map_err(|_| format!("Invalid duration value: {}", value_str))?;

    match unit.to_uppercase().as_str() {
        "S" => Ok(std::time::Duration::from_secs(value)),
        "M" => Ok(std::time::Duration::from_secs(value * 60)),
        "H" => Ok(std::time::Duration::from_secs(value * 3600)),
        _ => Err(format!("Unsupported duration unit: {}", unit)),
    }
}

// Internal async function that runs the actual schedule
async fn run_schedule(
    start_time: std::time::SystemTime,
    interval_str: &str,
    setpoints: Vec<i32>,
) -> Result<(), SchedulingError> {
    use chrono::{DateTime, Local};
    use std::time::SystemTime;

    let interval = parse_iso8601_duration(interval_str)?;

    // Calculate the initial delay and convert to tokio::time::Instant for precise timing
    let now_system = SystemTime::now();
    let now_instant = tokio::time::Instant::now();

    let initial_delay = start_time
        .duration_since(now_system)
        .map_err(|_| "Start time is in the past".to_string())?;

    let start_instant = now_instant + initial_delay;

    // Pre-calculate all absolute execution instants to avoid drift
    let mut execution_instants = Vec::new();
    let mut next_instant = start_instant;
    for _ in &setpoints {
        execution_instants.push(next_instant);
        next_instant += interval;
    }

    // Log start information
    let now_chrono: DateTime<Local> = now_system.into();
    let start_chrono: DateTime<Local> = start_time.into();

    info!("Current time: {}", now_chrono.format("%H:%M:%S.%6f"));
    info!("Start time: {}", start_chrono.format("%H:%M:%S.%6f"));
    info!("Waiting {:?} until start time...", initial_delay);

    // Execute each setpoint at its exact scheduled instant using sleep_until for precision
    for (i, &setpoint) in setpoints.iter().enumerate() {
        let target_instant = execution_instants[i];

        // Sleep until exact target instant (more precise than sleep with duration)
        tokio::time::sleep_until(target_instant).await;

        set_real_power_w(setpoint);
    }

    info!("Sequence complete!");
    Ok(())
}

// Upsert (create or replace) a control schedule
// This function cancels any existing schedule and starts a new one
pub async fn upsert_control_schedule(
    start_time: std::time::SystemTime,
    interval_str: &str,
    setpoints: Vec<i32>,
) -> Result<(), SchedulingError> {
    // Cancel previous schedule if exists
    {
        let mut current = CURRENT_SCHEDULE.lock().unwrap();
        if let Some(handle) = current.take() {
            handle.abort();
            info!(">> Cancelled previous schedule");
        }
    }

    // Spawn new schedule task
    let interval_str = interval_str.to_string();
    let handle = tokio::spawn(async move {
        if let Err(e) = run_schedule(start_time, &interval_str, setpoints).await {
            error!("Schedule error: {}", e);
        }
    });

    // Store the new async task handle
    {
        let mut current = CURRENT_SCHEDULE.lock().unwrap();
        *current = Some(handle);
    }

    Ok(())
}

// Calculate the next interval boundary from the current time with exact precision
// For example: if interval is "10S" and current time is 14:38:14.549870, returns 14:38:20.000000
// If interval is "1M" and current time is 14:38:14.549870, returns 14:39:00.000000
fn next_interval_mark(interval_str: &str) -> Result<std::time::SystemTime, SchedulingError> {
    use std::time::{Duration, SystemTime, UNIX_EPOCH};

    let interval = parse_iso8601_duration(interval_str)?;
    let interval_secs = interval.as_secs();

    let now = SystemTime::now();
    let since_epoch = now.duration_since(UNIX_EPOCH).unwrap();

    // Get whole seconds and fractional nanoseconds
    let total_secs = since_epoch.as_secs();
    let nanos = since_epoch.subsec_nanos();

    // If we have any fractional seconds, round up to the next whole second
    // This ensures we're always scheduling in the future
    let current_secs_rounded_up = if nanos > 0 {
        total_secs + 1
    } else {
        total_secs
    };

    // Calculate the next interval boundary from the rounded second
    let remainder = current_secs_rounded_up % interval_secs;
    let seconds_to_add = if remainder == 0 {
        interval_secs  // Already at boundary, go to next one
    } else {
        interval_secs - remainder
    };

    let target_secs = current_secs_rounded_up + seconds_to_add;

    // Create exact SystemTime at the boundary with zero fractional seconds
    Ok(UNIX_EPOCH + Duration::from_secs(target_secs))
}

// Example usage function demonstrating schedule override
#[tokio::main]
pub async fn run() {
    tracing_subscriber::fmt()
        .with_max_level(tracing::Level::DEBUG)
        .init();

    info!("=== Example: Schedule Override Demo ===");

    let interval_duration = "10S";

    // First schedule - 8 setpoints starting at next interval boundary
    let start_time1 = match next_interval_mark(interval_duration) {
        Ok(time) => time,
        Err(e) => {
            error!("Error calculating next interval mark: {}", e);
            return;
        }
    };
    let setpoints1 = vec![100, 200, 300, 400, 500, 600, 700, 800];

    info!("Creating first schedule with 8 setpoints (100-800 W):");
    if let Err(e) = upsert_control_schedule(start_time1, interval_duration, setpoints1).await {
        error!("Error: {}", e);
        return;
    }

    info!("Waiting 40 seconds before overriding with new schedule...");
    tokio::time::sleep(tokio::time::Duration::from_secs(40)).await;

    // Second schedule - overrides the first with new 8 setpoints at next interval boundary
    let start_time2 = match next_interval_mark(interval_duration) {
        Ok(time) => time,
        Err(e) => {
            error!("Error calculating next interval mark: {}", e);
            return;
        }
    };
    let setpoints2 = vec![80, 70, 60, 50, 40, 30, 20, 10];

    info!("Creating second schedule with 8 setpoints (10-80 W) - this will override the first:");
    if let Err(e) = upsert_control_schedule(start_time2, interval_duration, setpoints2).await {
        error!("Error: {}", e);
        return;
    }

    // Wait for the second schedule to complete
    tokio::time::sleep(tokio::time::Duration::from_secs(85)).await;
    info!("=== Demo Complete ===");
}
