import { useState, useRef } from 'react';
import { Card } from '../ui/Card';
import { Upload, FileText, FileSpreadsheet, Loader2, CheckCircle, XCircle, Sparkles } from 'lucide-react';
import { toast } from 'sonner';

interface AIQuestionGeneratorProps {
  onQuestionsGenerated: () => void;
}

export const AIQuestionGenerator = ({ onQuestionsGenerated }: AIQuestionGeneratorProps) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [category, setCategory] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<{
    status: 'idle' | 'uploading' | 'processing' | 'success' | 'error';
    message: string;
    totalSlides?: number;
    totalQuestions?: number;
  }>({ status: 'idle', message: '' });
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const fileType = file.name.toLowerCase();
      if (fileType.endsWith('.pdf') || fileType.endsWith('.ppt') || fileType.endsWith('.pptx')) {
        setSelectedFile(file);
        setUploadProgress({ status: 'idle', message: '' });
      } else {
        toast.error('Please upload a PDF or PowerPoint file');
      }
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    
    const file = e.dataTransfer.files[0];
    if (file) {
      const fileType = file.name.toLowerCase();
      if (fileType.endsWith('.pdf') || fileType.endsWith('.ppt') || fileType.endsWith('.pptx')) {
        setSelectedFile(file);
        setUploadProgress({ status: 'idle', message: '' });
      } else {
        toast.error('Please upload a PDF or PowerPoint file');
      }
    }
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleGenerate = async () => {
    if (!selectedFile) {
      toast.error('Please select a file first');
      return;
    }

    if (!category.trim()) {
      toast.error('Please enter a category for the questions');
      return;
    }

    try {
      setIsUploading(true);
      setUploadProgress({ status: 'uploading', message: 'Uploading file...' });

      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('category', category.trim());

      const token = localStorage.getItem('access_token');
      const response = await fetch('http://127.0.0.1:3001/api/questions/generate-from-file', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to generate questions');
      }

      setUploadProgress({ status: 'processing', message: 'Processing file and generating questions...' });

      const result = await response.json();
      
      setUploadProgress({
        status: 'success',
        message: `Successfully generated ${result.totalQuestions} questions from ${result.totalSlides} slides/pages!`,
        totalSlides: result.totalSlides,
        totalQuestions: result.totalQuestions,
      });

      toast.success(`Generated ${result.totalQuestions} questions successfully!`);
      
      // Notify parent to refresh questions
      setTimeout(() => {
        onQuestionsGenerated();
        // Reset form
        setSelectedFile(null);
        setCategory('');
        setUploadProgress({ status: 'idle', message: '' });
      }, 2000);

    } catch (error: any) {
      console.error('Error generating questions:', error);
      setUploadProgress({
        status: 'error',
        message: error.message || 'Failed to generate questions',
      });
      toast.error(error.message || 'Failed to generate questions');
    } finally {
      setIsUploading(false);
    }
  };

  const getFileIcon = () => {
    if (!selectedFile) return null;
    const fileName = selectedFile.name.toLowerCase();
    if (fileName.endsWith('.pdf')) {
      return <FileText className="h-8 w-8 text-red-500" />;
    }
    return <FileSpreadsheet className="h-8 w-8 text-orange-500" />;
  };

  return (
    <Card className="p-6 bg-gradient-to-br from-indigo-50 to-purple-50 border-2 border-indigo-200">
      <div className="flex items-center gap-3 mb-4">
        <div className="p-2 bg-indigo-600 rounded-lg">
          <Sparkles className="h-6 w-6 text-white" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-gray-900">AI Question Generator</h3>
          <p className="text-sm text-gray-600">Upload PDF or PowerPoint to auto-generate questions</p>
        </div>
      </div>

      {/* File Upload Area */}
      <div
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          selectedFile
            ? 'border-green-400 bg-green-50'
            : 'border-indigo-300 bg-white hover:border-indigo-400 hover:bg-indigo-50 cursor-pointer'
        }`}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        onClick={selectedFile ? undefined : handleUploadClick}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.ppt,.pptx"
          onChange={handleFileSelect}
          className="hidden"
        />

        {selectedFile ? (
          <div className="flex flex-col items-center gap-3">
            {getFileIcon()}
            <div>
              <p className="font-medium text-gray-900">{selectedFile.name}</p>
              <p className="text-sm text-gray-500">
                {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
              </p>
            </div>
            <button
              onClick={(e) => {
                e.stopPropagation();
                setSelectedFile(null);
                setUploadProgress({ status: 'idle', message: '' });
              }}
              className="text-sm text-red-600 hover:text-red-700 font-medium"
              disabled={isUploading}
            >
              Remove file
            </button>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3">
            <Upload className="h-12 w-12 text-indigo-400" />
            <div>
              <p className="font-medium text-gray-900">Drop your file here or click to browse</p>
              <p className="text-sm text-gray-500 mt-1">
                Supports PDF and PowerPoint (.ppt, .pptx) files
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Category Input */}
      <div className="mt-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Question Category <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          placeholder="e.g., Database Design, Web Development, Python Programming"
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          disabled={isUploading}
        />
      </div>

      {/* Progress Status */}
      {uploadProgress.status !== 'idle' && (
        <div className={`mt-4 p-4 rounded-lg ${
          uploadProgress.status === 'success' ? 'bg-green-100 border border-green-300' :
          uploadProgress.status === 'error' ? 'bg-red-100 border border-red-300' :
          'bg-blue-100 border border-blue-300'
        }`}>
          <div className="flex items-center gap-3">
            {uploadProgress.status === 'uploading' || uploadProgress.status === 'processing' ? (
              <Loader2 className="h-5 w-5 text-blue-600 animate-spin" />
            ) : uploadProgress.status === 'success' ? (
              <CheckCircle className="h-5 w-5 text-green-600" />
            ) : (
              <XCircle className="h-5 w-5 text-red-600" />
            )}
            <div>
              <p className={`font-medium ${
                uploadProgress.status === 'success' ? 'text-green-800' :
                uploadProgress.status === 'error' ? 'text-red-800' :
                'text-blue-800'
              }`}>
                {uploadProgress.message}
              </p>
              {uploadProgress.totalSlides && uploadProgress.totalQuestions && (
                <p className="text-sm text-green-700 mt-1">
                  {uploadProgress.totalSlides} slides/pages processed • {uploadProgress.totalQuestions} questions added to database
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Generate Button */}
      <button
        onClick={handleGenerate}
        disabled={!selectedFile || !category.trim() || isUploading}
        className={`mt-4 w-full py-3 px-4 rounded-lg font-medium transition-colors flex items-center justify-center gap-2 ${
          !selectedFile || !category.trim() || isUploading
            ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
            : 'bg-indigo-600 text-white hover:bg-indigo-700'
        }`}
      >
        {isUploading ? (
          <>
            <Loader2 className="h-5 w-5 animate-spin" />
            Generating Questions...
          </>
        ) : (
          <>
            <Sparkles className="h-5 w-5" />
            Generate Questions with AI
          </>
        )}
      </button>

      <p className="mt-3 text-xs text-gray-500 text-center">
        AI will extract content from each slide/page and generate MCQ questions automatically
      </p>
    </Card>
  );
};
