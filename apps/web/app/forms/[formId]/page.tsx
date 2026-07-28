import { FormDetailFeature } from "@/features/forms";

type FormDetailPageProps = {
  params: Promise<{
    formId: string;
  }>;
};

export default async function FormDetailPage({ params }: FormDetailPageProps) {
  const { formId } = await params;

  return <FormDetailFeature formId={formId} />;
}
