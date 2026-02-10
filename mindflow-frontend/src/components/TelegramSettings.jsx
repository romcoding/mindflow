/**
 * TelegramSettings - Telegram Bot Integration Settings
 * Allows users to configure their Telegram bot connection,
 * generate link tokens, and manage the integration.
 */
import React, { useState, useEffect } from 'react';
import { 
  MessageCircle, Link, Copy, Check, ExternalLink, RefreshCw, 
  AlertCircle, CheckCircle2, Settings, Loader2, Bot
} from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Badge } from './ui/badge';
import { telegramAPI } from '../lib/api';

const TelegramSettings = () => {
  const [botToken, setBotToken] = useState('');
  const [webhookUrl, setWebhookUrl] = useState('');
  const [linkToken, setLinkToken] = useState('');
  const [copied, setCopied] = useState(false);
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [setupLoading, setSetupLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Check current status on mount
  useEffect(() => {
    checkStatus();
  }, []);

  const checkStatus = async () => {
    try {
      setLoading(true);
      const response = await telegramAPI.getStatus();
      if (response.data?.success) {
        setStatus(response.data);
      }
    } catch (err) {
      console.log('Telegram status check:', err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSetup = async () => {
    if (!botToken.trim()) {
      setError('Please enter your Telegram bot token');
      return;
    }
    
    try {
      setSetupLoading(true);
      setError('');
      setSuccess('');
      
      const response = await telegramAPI.setup(botToken.trim(), webhookUrl.trim());
      
      if (response.data?.success) {
        setSuccess(`Bot @${response.data.bot?.username} connected successfully!`);
        setStatus(prev => ({ ...prev, configured: true, bot: response.data.bot }));
      } else {
        setError(response.data?.error || 'Setup failed');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to setup Telegram bot');
    } finally {
      setSetupLoading(false);
    }
  };

  const generateLinkToken = async () => {
    try {
      setError('');
      const response = await telegramAPI.generateLinkToken();
      
      if (response.data?.success) {
        setLinkToken(response.data.link_token);
      } else {
        setError(response.data?.error || 'Failed to generate token');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to generate link token');
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Status Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MessageCircle className="h-5 w-5 text-blue-500" />
            Telegram Integration
          </CardTitle>
          <CardDescription>
            Connect your Telegram account to manage tasks, contacts, and notes on the go.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
            <div className={`w-3 h-3 rounded-full ${
              status?.configured ? 'bg-green-500' : 'bg-gray-300'
            }`} />
            <div className="flex-1">
              <p className="font-medium text-sm">
                {status?.configured ? 'Bot Connected' : 'Not Connected'}
              </p>
              {status?.bot?.username && (
                <p className="text-xs text-gray-500">@{status.bot.username}</p>
              )}
            </div>
            <Button variant="ghost" size="sm" onClick={checkStatus} disabled={loading}>
              <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Setup Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Settings className="h-4 w-4" />
            Bot Setup
          </CardTitle>
          <CardDescription>
            Create a bot via <a href="https://t.me/BotFather" target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:underline">@BotFather</a> on Telegram, then enter the token below.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm font-medium text-gray-700 block mb-1">Bot Token</label>
            <input
              type="password"
              value={botToken}
              onChange={(e) => setBotToken(e.target.value)}
              placeholder="123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
              className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <p className="text-xs text-gray-400 mt-1">Get this from @BotFather on Telegram</p>
          </div>
          
          <div>
            <label className="text-sm font-medium text-gray-700 block mb-1">Webhook URL (Optional)</label>
            <input
              type="url"
              value={webhookUrl}
              onChange={(e) => setWebhookUrl(e.target.value)}
              placeholder="https://your-backend.com"
              className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <p className="text-xs text-gray-400 mt-1">Your MindFlow backend URL for receiving messages</p>
          </div>

          {error && (
            <div className="flex items-center gap-2 text-red-600 text-sm bg-red-50 p-3 rounded-lg">
              <AlertCircle className="h-4 w-4 flex-shrink-0" />
              {error}
            </div>
          )}
          
          {success && (
            <div className="flex items-center gap-2 text-green-600 text-sm bg-green-50 p-3 rounded-lg">
              <CheckCircle2 className="h-4 w-4 flex-shrink-0" />
              {success}
            </div>
          )}

          <Button onClick={handleSetup} disabled={setupLoading} className="w-full">
            {setupLoading ? (
              <><Loader2 className="h-4 w-4 mr-2 animate-spin" /> Connecting...</>
            ) : (
              <><MessageCircle className="h-4 w-4 mr-2" /> Connect Bot</>
            )}
          </Button>
        </CardContent>
      </Card>

      {/* Account Linking Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Link className="h-4 w-4" />
            Link Your Account
          </CardTitle>
          <CardDescription>
            Generate a one-time token to link your Telegram chat with your MindFlow account.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-3">
            <ol className="text-sm text-gray-600 space-y-2">
              <li className="flex items-start gap-2">
                <span className="bg-blue-100 text-blue-700 rounded-full w-5 h-5 flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5">1</span>
                <span>Click "Generate Token" below</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="bg-blue-100 text-blue-700 rounded-full w-5 h-5 flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5">2</span>
                <span>Open your MindFlow bot on Telegram</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="bg-blue-100 text-blue-700 rounded-full w-5 h-5 flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5">3</span>
                <span>Send: <code className="bg-gray-100 px-1 rounded">/link &lt;token&gt;</code></span>
              </li>
            </ol>
          </div>

          {linkToken && (
            <div className="bg-gray-50 rounded-lg p-3">
              <p className="text-xs text-gray-500 mb-1">Your link token (one-time use):</p>
              <div className="flex items-center gap-2">
                <code className="flex-1 text-sm bg-white border rounded px-2 py-1 font-mono break-all">
                  {linkToken}
                </code>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => copyToClipboard(`/link ${linkToken}`)}
                  className="flex-shrink-0"
                >
                  {copied ? <Check className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />}
                </Button>
              </div>
              <p className="text-xs text-gray-400 mt-2">
                Send to bot: <code className="bg-white px-1 rounded">/link {linkToken.substring(0, 8)}...</code>
              </p>
            </div>
          )}

          <Button variant="outline" onClick={generateLinkToken} className="w-full">
            <Link className="h-4 w-4 mr-2" />
            Generate Link Token
          </Button>
        </CardContent>
      </Card>

      {/* Usage Guide */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Bot className="h-4 w-4" />
            Bot Commands
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 text-sm">
            <div className="flex items-center gap-3 p-2 bg-gray-50 rounded">
              <code className="text-blue-600 font-mono text-xs min-w-[140px]">/task &lt;desc&gt;</code>
              <span className="text-gray-600">Create a new task</span>
            </div>
            <div className="flex items-center gap-3 p-2 bg-gray-50 rounded">
              <code className="text-blue-600 font-mono text-xs min-w-[140px]">/note &lt;content&gt;</code>
              <span className="text-gray-600">Save a note</span>
            </div>
            <div className="flex items-center gap-3 p-2 bg-gray-50 rounded">
              <code className="text-blue-600 font-mono text-xs min-w-[140px]">/stakeholder &lt;info&gt;</code>
              <span className="text-gray-600">Add a contact</span>
            </div>
            <div className="flex items-center gap-3 p-2 bg-gray-50 rounded">
              <code className="text-blue-600 font-mono text-xs min-w-[140px]">/status</code>
              <span className="text-gray-600">View dashboard stats</span>
            </div>
            <div className="flex items-center gap-3 p-2 bg-gray-50 rounded">
              <code className="text-blue-600 font-mono text-xs min-w-[140px]">/insights</code>
              <span className="text-gray-600">Get AI insights</span>
            </div>
            <div className="flex items-center gap-3 p-2 bg-gray-50 rounded">
              <code className="text-blue-600 font-mono text-xs min-w-[140px]">/ask &lt;question&gt;</code>
              <span className="text-gray-600">Ask the AI anything</span>
            </div>
            <p className="text-xs text-gray-400 mt-3">
              You can also send any free-form text — the AI will automatically classify it as a task, contact, note, or question.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default TelegramSettings;
