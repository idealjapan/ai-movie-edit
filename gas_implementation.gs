/**
 * Google Apps Script実装案
 * Google Drive + OpenAI APIを使用した簡易版
 */

// HTML UI
function doGet() {
  return HtmlService.createTemplateFromFile('index')
    .evaluate()
    .setTitle('AI動画編集ツール - GAS版')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

// 音声ファイル（事前抽出済み）をDriveから処理
function processAudioFromDrive(fileId) {
  try {
    // Google Driveから音声ファイルを取得
    const file = DriveApp.getFileById(fileId);
    const blob = file.getBlob();
    
    // OpenAI Whisper APIに送信
    const transcription = callWhisperAPI(blob);
    
    // GPT-4でキャプション整形
    const captions = formatCaptions(transcription.text);
    
    // SRTファイル生成
    const srtContent = generateSRT(captions, transcription.words);
    
    // Google Driveに保存
    const srtFile = DriveApp.createFile(
      file.getName().replace(/\.[^/.]+$/, "") + "_subtitles.srt",
      srtContent,
      MimeType.PLAIN_TEXT
    );
    
    return {
      success: true,
      srtFileId: srtFile.getId(),
      srtUrl: srtFile.getUrl()
    };
    
  } catch (error) {
    console.error('Error:', error);
    return {
      success: false,
      error: error.toString()
    };
  }
}

// OpenAI Whisper API呼び出し
function callWhisperAPI(audioBlob) {
  const apiKey = PropertiesService.getScriptProperties().getProperty('OPENAI_API_KEY');
  const url = 'https://api.openai.com/v1/audio/transcriptions';
  
  const formData = {
    'file': audioBlob,
    'model': 'whisper-1',
    'response_format': 'verbose_json',
    'timestamp_granularities[]': 'word',
    'language': 'ja'
  };
  
  const options = {
    'method': 'post',
    'headers': {
      'Authorization': 'Bearer ' + apiKey
    },
    'payload': formData
  };
  
  const response = UrlFetchApp.fetch(url, options);
  return JSON.parse(response.getContentText());
}

// GPT-4でキャプション整形
function formatCaptions(text) {
  const apiKey = PropertiesService.getScriptProperties().getProperty('OPENAI_API_KEY');
  const url = 'https://api.openai.com/v1/chat/completions';
  
  const messages = [{
    role: 'system',
    content: 'あなたは動画字幕の整形専門家です。'
  }, {
    role: 'user',
    content: `以下のテキストを字幕用に整形してください。
    1行20文字以内、フィラー語除去、句読点追加：\n\n${text}`
  }];
  
  const options = {
    'method': 'post',
    'headers': {
      'Authorization': 'Bearer ' + apiKey,
      'Content-Type': 'application/json'
    },
    'payload': JSON.stringify({
      'model': 'gpt-4',
      'messages': messages,
      'temperature': 0.7
    })
  };
  
  const response = UrlFetchApp.fetch(url, options);
  const result = JSON.parse(response.getContentText());
  return result.choices[0].message.content;
}

// SRTファイル生成
function generateSRT(formattedText, words) {
  // 簡易的な実装（実際はもっと複雑な処理が必要）
  const lines = formattedText.split('\n');
  let srtContent = '';
  let index = 1;
  
  lines.forEach((line, i) => {
    if (line.trim()) {
      const startTime = formatSRTTime(i * 3); // 仮の時間
      const endTime = formatSRTTime((i + 1) * 3);
      
      srtContent += `${index}\n`;
      srtContent += `${startTime} --> ${endTime}\n`;
      srtContent += `${line}\n\n`;
      index++;
    }
  });
  
  return srtContent;
}

// 時間フォーマット
function formatSRTTime(seconds) {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  const millis = Math.floor((seconds % 1) * 1000);
  
  return `${pad(hours)}:${pad(minutes)}:${pad(secs)},${pad(millis, 3)}`;
}

function pad(num, size = 2) {
  return num.toString().padStart(size, '0');
}

// EDL生成（音声ファイルの無音区間データが必要）
function generateEDLFromData(silenceData, duration) {
  let edlContent = 'TITLE: AI SILENCE CUT SEQUENCE\n';
  edlContent += 'FCM: NON-DROP FRAME\n\n';
  
  // 実装は省略（実際の無音検出ができないため）
  return edlContent;
}

// 設定画面
function getSettings() {
  const apiKey = PropertiesService.getScriptProperties().getProperty('OPENAI_API_KEY');
  return {
    hasApiKey: !!apiKey
  };
}

function saveApiKey(apiKey) {
  PropertiesService.getScriptProperties().setProperty('OPENAI_API_KEY', apiKey);
  return { success: true };
}