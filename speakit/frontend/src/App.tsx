import React, { ChangeEvent, DragEvent, FormEvent, useEffect, useMemo, useRef, useState } from 'react';

type Page = 'home' | 'upload' | 'dashboard' | 'preview' | 'analytics' | 'profile';

type AuthUser = {
  user_id: number;
  username: string;
  email: string;
  role: string;
  registration_date: string;
};

type OutputManifestItem = {
  target_language: string;
  label: string;
  output_path: string;
  audio_path?: string;
  audio_preview_url?: string;
  completed_at?: string;
  preview_url?: string;
  translation_engine?: string;
  synthesis_engine?: string;
  merge_engine?: string;
  is_demo_output?: boolean;
};

type VideoRecord = {
  video_id: number;
  user_id: number;
  video_title: string;
  file_path: string;
  upload_date: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  source_language: string;
  target_languages: string[];
  output_manifest: OutputManifestItem[];
  current_stage: string;
  progress: number;
  error_message?: string | null;
  logs: string[];
  storage_size: number;
  updated_at?: string;
  original_filename?: string;
  source_preview_url?: string;
  localized_outputs?: OutputManifestItem[];
};

type HistoryRecord = {
  history_id: number;
  video_id: number;
  source_language: string;
  target_language: string;
  transcription_accuracy: number;
  translation_accuracy: number;
  dubbing_quality: number;
  completion_date: string;
  transcript_text: string;
  translated_text: string;
  output_path?: string;
  segments: { start: number; end: number; text?: string; translated_text?: string }[];
};

type AnalyticsPayload = {
  analytics_id?: number;
  video_id?: number;
  processing_time?: number;
  word_count?: number;
  accuracy_score?: number;
  storage_size?: number;
  last_updated?: string;
  language_breakdown?: { target_language: string; label?: string; pair?: string }[];
  summary?: {
    videos_processed: number;
    completed_videos: number;
    average_accuracy: number;
    average_processing_time: number;
  };
  video_metrics?: Array<{
    video_id: number;
    video_title: string;
    status: string;
    current_stage: string;
    progress: number;
    processing_time: number;
    word_count: number;
    accuracy_score: number;
  }>;
  language_pairs?: Array<{
    target_language: string;
    transcription_accuracy: number;
    translation_accuracy: number;
    dubbing_quality: number;
  }>;
  activity_breakdown?: Array<{ status: string; total: number }>;
};

type FeedbackRecord = {
  feedback_id: number;
  user_id: number;
  comments: string;
  rating: number;
  feedback_date: string;
};

type ProfilePayload = {
  user: AuthUser;
  feedback: FeedbackRecord[];
};

type VideoDetailResponse = {
  video: VideoRecord;
  histories: HistoryRecord[];
  analytics: AnalyticsPayload | null;
};

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || getDefaultApiBaseUrl();
const BACKEND_ORIGIN = API_BASE_URL.replace(/\/api$/, '');
const DEMO_CREDENTIALS = {
  username: 'speakit_demo_user',
  email: 'speakit.demo@example.com',
  password: 'SpeakItDemo123!',
};
const ACCEPTED_VIDEO_TYPES = 'video/mp4,video/quicktime,video/x-matroska,video/webm,video/x-msvideo,video/x-m4v';
const ACCEPTED_VIDEO_EXTENSIONS = ['mp4', 'mov', 'mkv', 'webm', 'avi', 'm4v'];

const languageOptions = [
  { value: 'en', label: 'English' },
  { value: 'fr', label: 'French' },
  { value: 'es', label: 'Spanish' },
  { value: 'de', label: 'German' },
  { value: 'hi', label: 'Hindi' },
  { value: 'ja', label: 'Japanese' },
];

function App(): JSX.Element {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [page, setPage] = useState<Page>('home');
  const [backendHealthy, setBackendHealthy] = useState<boolean>(false);
  const [backendMessage, setBackendMessage] = useState<string>('Checking backend status...');
  const [authToken, setAuthToken] = useState<string>(localStorage.getItem('speakit_token') || '');
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(() => {
    const raw = localStorage.getItem('speakit_user');
    return raw ? JSON.parse(raw) : null;
  });
  const [authMessage, setAuthMessage] = useState<string>('Creating a demo session...');

  const [videoTitle, setVideoTitle] = useState<string>('');
  const [sourceLanguage, setSourceLanguage] = useState<string>('en');
  const [targetLanguages, setTargetLanguages] = useState<string[]>(['fr']);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDraggingVideo, setIsDraggingVideo] = useState<boolean>(false);
  const [uploading, setUploading] = useState<boolean>(false);
  const [uploadMessage, setUploadMessage] = useState<string>('Choose a video and start processing.');

  const [videos, setVideos] = useState<VideoRecord[]>([]);
  const [activeVideoId, setActiveVideoId] = useState<number | null>(null);
  const [activeDetail, setActiveDetail] = useState<VideoDetailResponse | null>(null);
  const [selectedOutputLanguage, setSelectedOutputLanguage] = useState<string>('');

  const [dashboardAnalytics, setDashboardAnalytics] = useState<AnalyticsPayload | null>(null);
  const [profile, setProfile] = useState<ProfilePayload | null>(null);
  const [feedbackRating, setFeedbackRating] = useState<number>(5);
  const [feedbackComments, setFeedbackComments] = useState<string>('');
  const [feedbackMessage, setFeedbackMessage] = useState<string>('');

  const navItems: { id: Page; label: string }[] = [
    { id: 'home', label: 'Home' },
    { id: 'upload', label: 'Upload' },
    { id: 'dashboard', label: 'Processing' },
    { id: 'preview', label: 'Preview' },
    { id: 'analytics', label: 'Analytics' },
    { id: 'profile', label: 'Profile' },
  ];

  const selectedVideo = useMemo(
    () => {
      if (activeDetail?.video.video_id === activeVideoId) {
        return activeDetail.video;
      }
      return videos.find((item) => item.video_id === activeVideoId) || null;
    },
    [videos, activeVideoId, activeDetail]
  );

  const activeHistory = useMemo(() => {
    if (!activeDetail?.histories.length) {
      return null;
    }
    return (
      activeDetail.histories.find((item) => item.target_language === selectedOutputLanguage) ||
      activeDetail.histories[0]
    );
  }, [activeDetail, selectedOutputLanguage]);

  const selectedOutput = useMemo(() => {
    const outputs = activeDetail?.video.localized_outputs || [];
    return (
      outputs.find((item) => item.target_language === selectedOutputLanguage) ||
      outputs[0] ||
      null
    );
  }, [activeDetail, selectedOutputLanguage]);

  useEffect(() => {
    void checkBackendHealth();
    const intervalId = window.setInterval(() => {
      void checkBackendHealth();
    }, 5000);
    return () => window.clearInterval(intervalId);
  }, []);

  useEffect(() => {
    if (backendHealthy) {
      void ensureDemoSession();
    }
  }, [backendHealthy]);

  useEffect(() => {
    if (!authToken || !currentUser) {
      return;
    }
    void Promise.all([loadVideos(authToken), loadAnalytics(currentUser.user_id, authToken), loadProfile(authToken)]);
  }, [authToken, currentUser]);

  useEffect(() => {
    if (!authToken || activeVideoId === null) {
      return;
    }
    void loadVideoDetail(activeVideoId, authToken);
    const intervalId = window.setInterval(() => {
      void Promise.all([loadVideoDetail(activeVideoId, authToken), loadVideos(authToken)]);
    }, 3000);
    return () => window.clearInterval(intervalId);
  }, [activeVideoId, authToken]);

  const toggleTargetLanguage = (value: string) => {
    setTargetLanguages((current) =>
      current.includes(value) ? current.filter((item) => item !== value) : [...current, value]
    );
  };

  const handleFileSelect = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0] || null;
    setVideoFile(file);
    event.target.value = '';
  };

  const handleBrowseVideo = () => {
    fileInputRef.current?.click();
  };

  const handleDragOver = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'copy';
    setIsDraggingVideo(true);
  };

  const handleDragLeave = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDraggingVideo(false);
  };

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDraggingVideo(false);
    setVideoFile(event.dataTransfer.files?.[0] || null);
  };

  const setVideoFile = (file: File | null) => {
    if (!file) {
      setSelectedFile(null);
      setUploadMessage('Choose a video and start processing.');
      return;
    }

    const extension = file.name.includes('.') ? file.name.split('.').pop()?.toLowerCase() || '' : '';
    if (!ACCEPTED_VIDEO_EXTENSIONS.includes(extension)) {
      setSelectedFile(null);
      setUploadMessage(`Unsupported video type. Use ${ACCEPTED_VIDEO_EXTENSIONS.map((item) => item.toUpperCase()).join(', ')}.`);
      return;
    }

    setSelectedFile(file);
    setUploadMessage(`${file.name} is ready to upload.`);
    if (!videoTitle.trim()) {
      setVideoTitle(file.name.replace(/\.[^/.]+$/, ''));
    }
  };

  async function handleStartProcessing(event: FormEvent): Promise<void> {
    event.preventDefault();
    if (!selectedFile) {
      setUploadMessage('Pick a video file before starting.');
      return;
    }
    if (!targetLanguages.length) {
      setUploadMessage('Choose at least one target language.');
      return;
    }
    if (!backendHealthy) {
      setUploadMessage('Checking backend connection...');
      const isBackendOnline = await checkBackendHealth();
      if (!isBackendOnline) {
        setUploadMessage('The Flask backend is offline. Start the backend and try again.');
        return;
      }
    }

    try {
      setUploading(true);
      setUploadMessage('Creating demo session...');
      const session = await ensureDemoSession();

      const formData = new FormData();
      formData.append('video', selectedFile);
      formData.append('video_title', videoTitle.trim() || selectedFile.name.replace(/\.[^/.]+$/, ''));
      formData.append('source_language', sourceLanguage);
      formData.append('target_languages', JSON.stringify(targetLanguages));

      setUploadMessage('Uploading video...');
      const uploadResponse = await apiFetch<{ message: string; video: VideoRecord }>(
        '/videos/upload',
        { method: 'POST', body: formData },
        session.token
      );

      setUploadMessage('Starting localization pipeline...');
      await apiFetch(`/videos/${uploadResponse.video.video_id}/process`, { method: 'POST' }, session.token);

      setVideos((current) => [
        uploadResponse.video,
        ...current.filter((item) => item.video_id !== uploadResponse.video.video_id),
      ]);
      setActiveVideoId(uploadResponse.video.video_id);
      setPage('dashboard');
      setUploadMessage('Processing started. Polling status now...');
      await Promise.all([
        loadVideos(session.token),
        loadVideoDetail(uploadResponse.video.video_id, session.token),
        currentUser ? loadAnalytics(currentUser.user_id, session.token) : Promise.resolve(),
      ]);
    } catch (error) {
      setUploadMessage(getErrorMessage(error));
    } finally {
      setUploading(false);
    }
  }

  async function handleFeedbackSubmit(event: FormEvent): Promise<void> {
    event.preventDefault();
    if (!authToken) {
      setFeedbackMessage('Sign-in session is missing. Refresh the page.');
      return;
    }

    try {
      const response = await apiFetch<{ message: string }>(
        '/feedback',
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ rating: feedbackRating, comments: feedbackComments }),
        },
        authToken
      );
      setFeedbackMessage(response.message);
      setFeedbackComments('');
      await loadProfile(authToken);
    } catch (error) {
      setFeedbackMessage(getErrorMessage(error));
    }
  }

  async function checkBackendHealth(): Promise<boolean> {
    try {
      const response = await fetch(`${BACKEND_ORIGIN}/health`);
      if (!response.ok) {
        throw new Error(`Backend health check failed with status ${response.status}.`);
      }
      setBackendHealthy(true);
      setBackendMessage('Backend is online.');
      return true;
    } catch (error) {
      setBackendHealthy(false);
      setBackendMessage(
        `Backend offline at ${BACKEND_ORIGIN}. Start the Flask app with npm run start:backend.`
      );
      return false;
    }
  }

  async function ensureDemoSession(): Promise<{ token: string; user: AuthUser }> {
    if (authToken && currentUser) {
      setAuthMessage(`Signed in as ${currentUser.username}.`);
      return { token: authToken, user: currentUser };
    }

    const loginPayload = {
      identifier: DEMO_CREDENTIALS.email,
      password: DEMO_CREDENTIALS.password,
    };

    let token = '';
    let user: AuthUser | null = null;

    try {
      const loginResponse = await apiFetch<{ token: string; user: AuthUser }>('/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(loginPayload),
      });
      token = loginResponse.token;
      user = loginResponse.user;
    } catch (loginError) {
      const response = await fetch(`${API_BASE_URL}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(DEMO_CREDENTIALS),
      });

      if (response.status === 409) {
        const retry = await apiFetch<{ token: string; user: AuthUser }>('/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(loginPayload),
        });
        token = retry.token;
        user = retry.user;
      } else if (response.ok) {
        const registered: { token: string; user: AuthUser } = await response.json();
        token = registered.token;
        user = registered.user;
      } else {
        throw new Error(getErrorMessage(loginError));
      }
    }

    if (!token || !user) {
      throw new Error('Unable to create a demo session.');
    }

    setAuthToken(token);
    setCurrentUser(user);
    localStorage.setItem('speakit_token', token);
    localStorage.setItem('speakit_user', JSON.stringify(user));
    setAuthMessage(`Signed in as ${user.username}.`);
    return { token, user };
  }

  async function loadVideos(tokenToUse: string): Promise<void> {
    const response = await apiFetch<{ videos: VideoRecord[] }>('/videos', {}, tokenToUse);
    setVideos(response.videos);
    if (activeVideoId === null && response.videos.length) {
      setActiveVideoId(response.videos[0].video_id);
    }
  }

  async function loadVideoDetail(videoId: number, tokenToUse: string): Promise<void> {
    const response = await apiFetch<VideoDetailResponse>(`/videos/${videoId}`, {}, tokenToUse);
    setActiveDetail(response);
    setVideos((current) => {
      const nextVideo = response.video;
      const exists = current.some((item) => item.video_id === nextVideo.video_id);
      if (!exists) {
        return [nextVideo, ...current];
      }
      return current.map((item) => (item.video_id === nextVideo.video_id ? nextVideo : item));
    });
    setSelectedOutputLanguage((current) => current || response.histories[0]?.target_language || '');
  }

  async function loadAnalytics(userId: number, tokenToUse: string): Promise<void> {
    const response = await apiFetch<AnalyticsPayload>(`/analytics/${userId}`, {}, tokenToUse);
    setDashboardAnalytics(response);
  }

  async function loadProfile(tokenToUse: string): Promise<void> {
    const response = await apiFetch<ProfilePayload>('/auth/profile', {}, tokenToUse);
    setProfile(response);
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">AI-Powered Video Localization</p>
          <h1>SpeakIt</h1>
          <p className="status-line">{backendMessage}</p>
          <p className="status-line">{authMessage}</p>
        </div>
        <nav className="nav">
          {navItems.map((item) => (
            <button
              key={item.id}
              className={page === item.id ? 'nav-button active' : 'nav-button'}
              onClick={() => setPage(item.id)}
              type="button"
            >
              {item.label}
            </button>
          ))}
        </nav>
      </header>

      <main className="main-grid">
        <section className="hero-card">
          <p className="kicker">Break language barriers with AI</p>
          <h2>Upload a video, watch the pipeline run, and read the transcript as soon as processing finishes.</h2>
          <p className="hero-copy">
            This version is connected to the Flask backend. If the backend is running on port 5000,
            the upload form below will create a demo user, send the video to the API, start the AVLA
            pipeline, and poll until transcript data is available.
          </p>
          <div className="hero-actions">
            <button type="button" className="primary-button" onClick={() => setPage('upload')}>
              Upload A Video
            </button>
            <button type="button" className="secondary-button" onClick={() => setPage('dashboard')}>
              Watch Processing
            </button>
          </div>
          <div className="feature-strip">
            <div className="feature-pill">Transcribe</div>
            <div className="feature-pill">Translate</div>
            <div className="feature-pill">Dub</div>
          </div>
        </section>

        <section className="panel-stack">
          <article className="panel">
            <h3>Current Upload</h3>
            <p>Source: {languageOptions.find((item) => item.value === sourceLanguage)?.label}</p>
            <p>
              Targets:{' '}
              {targetLanguages.length
                ? targetLanguages
                    .map((item) => languageOptions.find((lang) => lang.value === item)?.label || item)
                    .join(', ')
                : 'None selected'}
            </p>
            <p>File: {selectedFile?.name || 'No file selected'}</p>
          </article>
          <article className="panel">
            <h3>Active Status</h3>
            <p>{selectedVideo?.video_title || 'No project selected yet'}</p>
            <p>{formatStage(selectedVideo?.current_stage || 'waiting')}</p>
            <div className="progress-track">
              <div className="progress-fill" style={{ width: `${selectedVideo?.progress || 0}%` }} />
            </div>
            <p className="status-line">{selectedVideo?.error_message || uploadMessage}</p>
          </article>
        </section>
      </main>

      <section className="content-card">
        {page === 'home' && (
          <div className="grid-two">
            <article className="panel">
              <h3>How it works</h3>
              <ol className="steps">
                <li>Pick an English video and choose one or more target languages.</li>
                <li>SpeakIt uploads the file, starts the background pipeline, and polls for updates.</li>
                <li>When the run completes, the transcript, translations, analytics, and output files appear below.</li>
              </ol>
            </article>
            <article className="panel">
              <h3>Supported language pairs</h3>
              <ul className="plain-list">
                <li>English to French</li>
                <li>English to Spanish</li>
                <li>English to German</li>
                <li>English to Hindi</li>
                <li>English to Japanese</li>
              </ul>
            </article>
          </div>
        )}

        {page === 'upload' && (
          <div className="grid-two">
            <article className="panel">
              <h3>Upload Video</h3>
              <form onSubmit={handleStartProcessing}>
                <label className="input-label">
                  Video title
                  <input
                    className="text-input"
                    value={videoTitle}
                    onChange={(event) => setVideoTitle(event.target.value)}
                    placeholder="Launch announcement"
                  />
                </label>
                <label className="input-label">
                  Source language
                  <select
                    className="text-input"
                    value={sourceLanguage}
                    onChange={(event) => setSourceLanguage(event.target.value)}
                  >
                    {languageOptions.map((language) => (
                      <option key={language.value} value={language.value}>
                        {language.label}
                      </option>
                    ))}
                  </select>
                </label>
                <div className="input-label">
                  Target languages
                  <div className="chip-grid">
                    {languageOptions
                      .filter((language) => language.value !== 'en')
                      .map((language) => (
                        <button
                          key={language.value}
                          type="button"
                          className={targetLanguages.includes(language.value) ? 'chip active' : 'chip'}
                          onClick={() => toggleTargetLanguage(language.value)}
                        >
                          {language.label}
                        </button>
                      ))}
                  </div>
                </div>
                <div
                  className={isDraggingVideo ? 'upload-box active' : 'upload-box'}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                >
                  <input
                    ref={fileInputRef}
                    className="file-input"
                    type="file"
                    accept={ACCEPTED_VIDEO_TYPES}
                    onChange={handleFileSelect}
                  />
                  <span>Drag a video here</span>
                  <strong>{selectedFile?.name || 'No file selected'}</strong>
                  <button type="button" className="secondary-button browse-button" onClick={handleBrowseVideo}>
                    Browse Video
                  </button>
                </div>
                <button type="submit" className="primary-button" disabled={uploading}>
                  {uploading ? 'Processing...' : 'Start Processing'}
                </button>
                <p className="status-line">{uploadMessage}</p>
              </form>
            </article>
            <article className="panel">
              <h3>What happens next</h3>
              <ul className="plain-list">
                <li>Audio extraction begins immediately after the upload finishes.</li>
                <li>The backend runs transcription before translation and dubbing.</li>
                <li>Dashboard logs update every 3 seconds while the pipeline is running.</li>
                <li>The preview tab shows transcript text and downloadable outputs after completion.</li>
              </ul>
            </article>
          </div>
        )}

        {page === 'dashboard' && (
          <div className="grid-two">
            <article className="panel">
              <h3>Your Projects</h3>
              {videos.length ? (
                <div className="project-list">
                  {videos.map((project) => (
                    <button
                      key={project.video_id}
                      type="button"
                      className={activeVideoId === project.video_id ? 'project-card active' : 'project-card'}
                      onClick={() => {
                        setActiveVideoId(project.video_id);
                        setPage('dashboard');
                      }}
                    >
                      <strong>{project.video_title}</strong>
                      <span>{project.status.toUpperCase()}</span>
                      <span>{formatStage(project.current_stage)}</span>
                      <span>{project.progress}%</span>
                    </button>
                  ))}
                </div>
              ) : (
                <p className="status-line">No uploads yet. Start with the Upload tab.</p>
              )}
            </article>
            <article className="panel">
              <h3>Pipeline Stages</h3>
              <ul className="plain-list">
                <li>Extracting Audio</li>
                <li>Transcribing</li>
                <li>Translating</li>
                <li>Dubbing</li>
                <li>Merging</li>
              </ul>
              <div className="log-box">
                {selectedVideo?.logs?.length ? (
                  selectedVideo.logs.slice().reverse().map((log) => <p key={log}>{log}</p>)
                ) : (
                  <p>Logs will appear here once processing starts.</p>
                )}
              </div>
            </article>
          </div>
        )}

        {page === 'preview' && (
          <div className="grid-two">
            <article className="panel">
              <h3>Preview & Export</h3>
              {activeDetail?.video.source_preview_url ? (
                <div className="media-stack">
                  <div className="media-group">
                    <p className="media-label">Original</p>
                    <video className="media-player" controls src={resolveAssetUrl(activeDetail.video.source_preview_url)} />
                  </div>
                  {activeDetail.video.localized_outputs?.length ? (
                    <>
                      <div className="chip-grid">
                        {activeDetail.video.localized_outputs.map((item) => (
                          <button
                            key={item.target_language}
                            type="button"
                            className={selectedOutputLanguage === item.target_language ? 'chip active' : 'chip'}
                            onClick={() => setSelectedOutputLanguage(item.target_language)}
                          >
                            {item.label}
                          </button>
                        ))}
                      </div>
                      <div className="media-group">
                        <p className="media-label">
                          Localized{' '}
                          {selectedOutput?.label || ''}
                        </p>
                        <video
                          className="media-player"
                          controls
                          src={resolveAssetUrl(selectedOutput?.preview_url || '')}
                        />
                        {selectedOutput?.is_demo_output && (
                          <p className="status-line">
                            Demo mode copied the original video, so this preview keeps the original English audio.
                            Use the translated text below as the French demo output.
                          </p>
                        )}
                      </div>
                      {selectedOutput?.audio_preview_url && (
                        <div className="media-group">
                          <p className="media-label">Dubbed Audio Artifact</p>
                          <audio
                            className="audio-player"
                            controls
                            src={resolveAssetUrl(selectedOutput.audio_preview_url)}
                          />
                          <p className="status-line">
                            Engine: {selectedOutput.synthesis_engine || 'unknown'}
                          </p>
                        </div>
                      )}
                      <a
                        className="download-link"
                        href={resolveAssetUrl(selectedOutput?.preview_url || '')}
                      >
                        Download Localized Video
                      </a>
                    </>
                  ) : (
                    <div className="video-placeholder">Localized video will appear after processing completes.</div>
                  )}
                </div>
              ) : (
                <div className="video-placeholder">Upload a video to unlock preview mode.</div>
              )}
            </article>
            <article className="panel">
              <h3>Transcript</h3>
              {activeHistory ? (
                <>
                  <p className="detail-copy">{activeHistory.transcript_text}</p>
                  <h3>Translated Text</h3>
                  <p className="detail-copy">{activeHistory.translated_text}</p>
                  <h3>Segments</h3>
                  <div className="log-box">
                    {activeHistory.segments.length ? (
                      activeHistory.segments.map((segment, index) => (
                        <p key={`${segment.start}-${segment.end}-${index}`}>
                          [{segment.start.toFixed(1)}s - {segment.end.toFixed(1)}s] {segment.translated_text || segment.text}
                        </p>
                      ))
                    ) : (
                      <p>No segments available yet.</p>
                    )}
                  </div>
                </>
              ) : (
                <p className="status-line">Transcript text will appear here after the pipeline reaches translation.</p>
              )}
            </article>
          </div>
        )}

        {page === 'analytics' && (
          <div className="grid-three">
            <article className="panel metric">
              <span>Videos Processed</span>
              <strong>{dashboardAnalytics?.summary?.videos_processed || 0}</strong>
            </article>
            <article className="panel metric">
              <span>Avg Accuracy</span>
              <strong>{toPercent(dashboardAnalytics?.summary?.average_accuracy)}</strong>
            </article>
            <article className="panel metric">
              <span>Avg Time</span>
              <strong>{dashboardAnalytics?.summary?.average_processing_time || 0}m</strong>
            </article>
            <article className="panel">
              <h3>Language Pair Scores</h3>
              <div className="bar-group">
                {dashboardAnalytics?.language_pairs?.length ? (
                  dashboardAnalytics.language_pairs.map((item) => (
                    <div key={item.target_language} className="bar-row">
                      <span>EN-{item.target_language.toUpperCase()}</span>
                      <div className="bar">
                        <div style={{ width: `${Math.round(item.translation_accuracy * 100)}%` }} />
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="status-line">Analytics populate after at least one completed video.</p>
                )}
              </div>
            </article>
            <article className="panel">
              <h3>Selected Video</h3>
              <p>Word Count: {activeDetail?.analytics?.word_count || 0}</p>
              <p>Accuracy Score: {toPercent(activeDetail?.analytics?.accuracy_score)}</p>
              <p>Storage Size: {activeDetail?.analytics?.storage_size || 0} MB</p>
            </article>
            <article className="panel">
              <h3>Activity</h3>
              {dashboardAnalytics?.activity_breakdown?.length ? (
                dashboardAnalytics.activity_breakdown.map((item) => (
                  <p key={item.status}>
                    {item.status}: {item.total}
                  </p>
                ))
              ) : (
                <p>No activity data yet.</p>
              )}
            </article>
          </div>
        )}

        {page === 'profile' && (
          <div className="grid-two">
            <article className="panel">
              <h3>Profile</h3>
              <p>Name: {profile?.user.username || currentUser?.username || 'Demo User'}</p>
              <p>Email: {profile?.user.email || currentUser?.email || 'Unknown'}</p>
              <p>Role: {profile?.user.role || currentUser?.role || 'user'}</p>
              <h3>Feedback History</h3>
              <div className="log-box">
                {profile?.feedback?.length ? (
                  profile.feedback.map((item) => (
                    <p key={item.feedback_id}>
                      {item.rating}/5 on {new Date(item.feedback_date).toLocaleString()}: {item.comments || 'No comment'}
                    </p>
                  ))
                ) : (
                  <p>No feedback submitted yet.</p>
                )}
              </div>
            </article>
            <article className="panel">
              <h3>Feedback</h3>
              <form onSubmit={handleFeedbackSubmit}>
                <label className="input-label">
                  Rating
                  <select
                    className="text-input"
                    value={feedbackRating}
                    onChange={(event) => setFeedbackRating(Number(event.target.value))}
                  >
                    <option value="5">5 - Excellent</option>
                    <option value="4">4 - Good</option>
                    <option value="3">3 - Okay</option>
                    <option value="2">2 - Needs work</option>
                    <option value="1">1 - Poor</option>
                  </select>
                </label>
                <label className="input-label">
                  Comments
                  <textarea
                    className="text-area"
                    rows={4}
                    value={feedbackComments}
                    onChange={(event) => setFeedbackComments(event.target.value)}
                    placeholder="Share your experience..."
                  />
                </label>
                <button type="submit" className="primary-button">
                  Submit Feedback
                </button>
                <p className="status-line">{feedbackMessage}</p>
              </form>
            </article>
          </div>
        )}
      </section>
    </div>
  );
}

async function apiFetch<T = unknown>(path: string, init: RequestInit = {}, token?: string): Promise<T> {
  const headers = new Headers(init.headers || {});
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  if (!(init.body instanceof FormData) && !headers.has('Content-Type') && init.body) {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(`${API_BASE_URL}${path}`, { ...init, headers });
  const contentType = response.headers.get('content-type') || '';
  const data = contentType.includes('application/json') ? await response.json() : await response.text();

  if (!response.ok) {
    if (typeof data === 'string') {
      throw new Error(data);
    }
    throw new Error((data && typeof data === 'object' && 'message' in data ? String(data.message) : '') || `Request failed with status ${response.status}.`);
  }

  return data;
}

function getErrorMessage(error: unknown): string {
  if (error instanceof TypeError && error.message.toLowerCase().includes('fetch')) {
    return `Cannot reach the backend at ${BACKEND_ORIGIN}. Make sure Flask is running on port 5000, then refresh the page.`;
  }
  return error instanceof Error ? error.message : 'Something went wrong.';
}

function formatStage(stage: string): string {
  return stage.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase());
}

function toPercent(value?: number): string {
  if (typeof value !== 'number') {
    return '0%';
  }
  return `${Math.round(value * 100)}%`;
}

function resolveAssetUrl(path: string): string {
  if (!path) {
    return '';
  }
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path;
  }
  return `${BACKEND_ORIGIN}${path}`;
}

function getDefaultApiBaseUrl(): string {
  if (typeof window === 'undefined') {
    return 'http://localhost:5000/api';
  }
  return `${window.location.protocol}//${window.location.hostname}:5000/api`;
}

export default App;
