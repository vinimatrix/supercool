use axum::{
    extract::State,
    http::StatusCode,
    routing::{get, post},
    Json, Router,
};
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use tokio::sync::Mutex;
use tracing_subscriber;

mod ffmpeg;
mod lib;
mod pipeline;

#[derive(Clone)]
struct AppState {
    working_dir: Arc<Mutex<String>>,
}

#[derive(Deserialize)]
struct ConcatRequest {
    clips: Vec<String>,
    output: String,
}

#[derive(Deserialize)]
struct TranscodeRequest {
    input: String,
    output: String,
    fps: Option<u32>,
}

#[derive(Deserialize)]
struct MixAudioRequest {
    dialogue: String,
    music: String,
    output: String,
    ducking: Option<bool>,
}

#[derive(Deserialize)]
struct PipelineRequest {
    scenes: Vec<pipeline::Scene>,
    output: String,
    fps: Option<u32>,
}

#[derive(Serialize)]
struct HealthResponse {
    status: String,
    ffmpeg_available: bool,
}

#[derive(Serialize)]
struct OperationResponse {
    success: bool,
    output: String,
    message: String,
}

async fn health() -> Json<HealthResponse> {
    let ffmpeg_available = ffmpeg::check_ffmpeg_available();
    Json(HealthResponse {
        status: "ok".to_string(),
        ffmpeg_available,
    })
}

async fn concat_handler(
    State(state): State<AppState>,
    Json(request): Json<ConcatRequest>,
) -> Result<Json<OperationResponse>, StatusCode> {
    let working_dir = state.working_dir.lock().await.clone();
    let output_path = format!("{}/{}", working_dir, request.output);
    
    match ffmpeg::concat::concat_clips(&request.clips, &output_path, &working_dir).await {
        Ok(_) => Ok(Json(OperationResponse {
            success: true,
            output: output_path,
            message: "Clips concatenated successfully".to_string(),
        })),
        Err(e) => Err(StatusCode::INTERNAL_SERVER_ERROR),
    }
}

async fn transcode_handler(
    State(state): State<AppState>,
    Json(request): Json<TranscodeRequest>,
) -> Result<Json<OperationResponse>, StatusCode> {
    let working_dir = state.working_dir.lock().await.clone();
    let input_path = format!("{}/{}", working_dir, request.input);
    let output_path = format!("{}/{}", working_dir, request.output);
    let fps = request.fps.unwrap_or(24);
    
    match ffmpeg::transcode::transcode_to_24fps(&input_path, &output_path, fps).await {
        Ok(_) => Ok(Json(OperationResponse {
            success: true,
            output: output_path,
            message: format!("Video transcoded to {}fps", fps),
        })),
        Err(e) => Err(StatusCode::INTERNAL_SERVER_ERROR),
    }
}

async fn mix_audio_handler(
    State(state): State<AppState>,
    Json(request): Json<MixAudioRequest>,
) -> Result<Json<OperationResponse>, StatusCode> {
    let working_dir = state.working_dir.lock().await.clone();
    let dialogue_path = format!("{}/{}", working_dir, request.dialogue);
    let music_path = format!("{}/{}", working_dir, request.music);
    let output_path = format!("{}/{}", working_dir, request.output);
    
    match ffmpeg::audio::mix_audio(&dialogue_path, &music_path, &output_path, request.ducking.unwrap_or(false)).await {
        Ok(_) => Ok(Json(OperationResponse {
            success: true,
            output: output_path,
            message: "Audio mixed successfully".to_string(),
        })),
        Err(e) => Err(StatusCode::INTERNAL_SERVER_ERROR),
    }
}

async fn pipeline_handler(
    State(state): State<AppState>,
    Json(request): Json<PipelineRequest>,
) -> Result<Json<OperationResponse>, StatusCode> {
    let working_dir = state.working_dir.lock().await.clone();
    let fps = request.fps.unwrap_or(24);
    
    match pipeline::run_pipeline(&request.scenes, &request.output, &working_dir, fps).await {
        Ok(_) => Ok(Json(OperationResponse {
            success: true,
            output: request.output,
            message: "Pipeline completed successfully".to_string(),
        })),
        Err(e) => Err(StatusCode::INTERNAL_SERVER_ERROR),
    }
}

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt::init();
    
    let state = AppState {
        working_dir: Arc::new(Mutex::new("/tmp/supercool-nle".to_string())),
    };
    
    let app = Router::new()
        .route("/nle/health", get(health))
        .route("/nle/concat", post(concat_handler))
        .route("/nle/transcode", post(transcode_handler))
        .route("/nle/mix-audio", post(mix_audio_handler))
        .route("/nle/pipeline", post(pipeline_handler))
        .with_state(state);
    
    let listener = tokio::net::TcpListener::bind("0.0.0.0:3001").await.unwrap();
    tracing::info!("NLE engine listening on port 3001");
    axum::serve(listener, app).await.unwrap();
}