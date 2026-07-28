import { JobDetailFeature } from "@/features/jobs";

type JobDetailPageProps = {
  params: Promise<{
    jobId: string;
  }>;
};

export default async function JobDetailPage({ params }: JobDetailPageProps) {
  const { jobId } = await params;

  return <JobDetailFeature jobId={jobId} />;
}
