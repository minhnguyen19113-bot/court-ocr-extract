import { ReviewDetailFeature } from "@/features/review";

type ReviewDetailPageProps = {
  params: Promise<{
    reviewId: string;
  }>;
};

export default async function ReviewDetailPage({ params }: ReviewDetailPageProps) {
  const { reviewId } = await params;

  return <ReviewDetailFeature reviewId={reviewId} />;
}
