import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { MessageSquare, FileText, BarChart3, DatabaseZap, ClockAlert } from 'lucide-react'
import { Layout } from '@/components/shared/layout'
import { ChatPanel } from '@/components/chat/chat-panel'
import { DocumentList } from '@/components/documents/document-list'
import { EvalDashboard } from '@/components/dashboard/eval-dashboard'
import { DowntimeHistory } from '@/components/dashboard/downtime-history'

function App() {
  return (
    <Layout>
      <div className="flex items-center gap-3 mb-6 bg-[#020617] border border-border p-4 rounded-xl shadow-inner w-fit">
        <div className="w-8 h-8 rounded-lg bg-primary/10 border border-primary/30 flex items-center justify-center text-primary">
          <DatabaseZap className="h-4 w-4" />
        </div>
        <div>
          <h2 className="text-xs font-bold text-foreground uppercase tracking-widest">Workspace Telemetry</h2>
          <p className="text-[10px] text-muted-foreground font-mono mt-0.5">Control panel for document ingestion & conversational generative engine</p>
        </div>
      </div>

      <div className="bg-card border border-border rounded-xl shadow-2xl overflow-hidden relative z-0">
        <Tabs defaultValue="chat" className="flex flex-col w-full">
          <div className="bg-[#020617]/50 border-b border-border w-full flex overflow-x-auto pt-2 px-2 pb-0 items-end">
            <TabsList className="bg-transparent gap-1 p-0 h-auto">
              <TabsTrigger value="chat" className="data-active:bg-card data-active:border-border data-active:border-x data-active:border-t data-active:text-primary rounded-b-none rounded-t-lg py-3 px-6 text-sm font-mono tracking-tight font-semibold shadow-none border border-transparent transition-all">
                <MessageSquare className="mr-2 h-4 w-4" />
                Conversational Agent
              </TabsTrigger>
              <TabsTrigger value="documents" className="data-active:bg-card data-active:border-border data-active:border-x data-active:border-t data-active:text-primary rounded-b-none rounded-t-lg py-3 px-6 text-sm font-mono tracking-tight font-semibold shadow-none border border-transparent transition-all">
                <FileText className="mr-2 h-4 w-4" />
                Vector KB (Docs)
              </TabsTrigger>
              <TabsTrigger value="dashboard" className="data-active:bg-card data-active:border-border data-active:border-x data-active:border-t data-active:text-primary rounded-b-none rounded-t-lg py-3 px-6 text-sm font-mono tracking-tight font-semibold shadow-none border border-transparent transition-all">
                <BarChart3 className="mr-2 h-4 w-4" />
                Ragas Evaluation
              </TabsTrigger>
              <TabsTrigger value="downtime" className="data-active:bg-card data-active:border-border data-active:border-x data-active:border-t data-active:text-destructive rounded-b-none rounded-t-lg py-3 px-6 text-sm font-mono tracking-tight font-semibold shadow-none border border-transparent transition-all">
                <ClockAlert className="mr-2 h-4 w-4" />
                Downtime History
              </TabsTrigger>
            </TabsList>
          </div>
          <div className="p-6 md:p-8 min-h-[500px]">
            <TabsContent value="chat" className="h-full">
              <ChatPanel />
            </TabsContent>
            <TabsContent value="documents" className="h-full">
              <DocumentList />
            </TabsContent>
            <TabsContent value="dashboard" className="h-full">
              <EvalDashboard />
            </TabsContent>
            <TabsContent value="downtime" className="h-full">
              <DowntimeHistory />
            </TabsContent>
          </div>
        </Tabs>
      </div>
    </Layout>
  )
}

export default App
