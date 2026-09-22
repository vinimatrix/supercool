#include <stdarg.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdlib.h>

/**
 * Scene structure for pipeline
 */
typedef struct DriftScene {
  const char *const *clips;
  uintptr_t clip_count;
  const char *output;
} DriftScene;

/**
 * Check if FFmpeg is available on the system
 */
bool drift_check_ffmpeg(void);

/**
 * Get version string
 */
char *drift_version(void);

/**
 * Free a string returned by drift functions
 */
void drift_free_string(char *s);

/**
 * Concatenate video clips into a single output file
 */
bool drift_concat_clips(const char *const *clips, uintptr_t clip_count, const char *output);

/**
 * Transcode video with frame rate conversion
 */
bool drift_transcode(const char *input, const char *output, uint32_t fps);

/**
 * Mix multiple audio tracks into a single output
 */
bool drift_mix_audio(const char *const *tracks,
                     uintptr_t track_count,
                     const char *output,
                     bool ducking);

/**
 * Run a full render pipeline
 */
bool drift_run_pipeline(const struct DriftScene *scenes,
                        uintptr_t scene_count,
                        const char *output,
                        uint32_t _fps);
